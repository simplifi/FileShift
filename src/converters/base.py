"""
Base classes and interfaces for format handlers.
"""
import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterator, Dict, Any, List, Optional, Set
from dataclasses import dataclass
from enum import Enum


class FileFormat(Enum):
    """Supported file formats."""
    JSON = "json"
    JSONL = "jsonl"
    CSV = "csv"
    UNKNOWN = "unknown"


@dataclass
class ConversionOptions:
    """Options for file conversion."""
    encoding: str = "utf-8"
    delimiter: str = ","
    quotechar: str = '"'
    flatten_nested: bool = True
    nested_separator: str = "."
    preserve_types: bool = True
    skip_errors: bool = False
    chunk_size: int = 1000
    selected_fields: Optional[List[str]] = None


@dataclass
class FileMetadata:
    """Metadata about a file."""
    format: FileFormat
    encoding: str
    line_ending: str
    size_bytes: int
    estimated_records: int
    detected_fields: Set[str]
    sample_records: List[Dict[str, Any]]


class FormatHandler(ABC):
    """Abstract base class for format handlers."""
    
    def __init__(self, options: Optional[ConversionOptions] = None):
        self.options = options or ConversionOptions()
    
    @abstractmethod
    def can_handle(self, file_path: Path) -> bool:
        """Check if this handler can process the given file."""
        pass
    
    @abstractmethod
    def detect_metadata(self, file_path: Path) -> FileMetadata:
        """Detect and return metadata about the file."""
        pass
    
    @abstractmethod
    def read_records(self, file_path: Path) -> Iterator[Dict[str, Any]]:
        """Read records from the file as an iterator."""
        pass
    
    @abstractmethod
    def write_records(self, records: Iterator[Dict[str, Any]], output_path: Path) -> int:
        """Write records to the output file. Returns number of records written."""
        pass
    
    def extract_fields(self, record: Dict[str, Any], prefix: str = "") -> Set[str]:
        """Extract all field paths from a record."""
        fields = set()
        
        if not isinstance(record, dict):
            return fields
        
        for key, value in record.items():
            field_path = f"{prefix}{self.options.nested_separator}{key}" if prefix else key
            fields.add(field_path)
            
            if isinstance(value, dict) and self.options.flatten_nested:
                nested_fields = self.extract_fields(value, field_path)
                fields.update(nested_fields)
            elif isinstance(value, list):
                # For lists, we just note the field exists
                # More sophisticated handling could inspect list contents
                pass
        
        return fields
    
    def flatten_record(self, record: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
        """Flatten a nested record using dot notation."""
        if not self.options.flatten_nested:
            return record
        
        flattened = {}
        
        def _flatten(obj: Any, current_prefix: str):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_key = f"{current_prefix}{self.options.nested_separator}{key}" if current_prefix else key
                    if isinstance(value, dict):
                        _flatten(value, new_key)
                    elif isinstance(value, list):
                        # Convert lists to JSON strings for CSV compatibility
                        flattened[new_key] = json.dumps(value) if value else ""
                    else:
                        flattened[new_key] = value
            else:
                flattened[current_prefix] = obj
        
        _flatten(record, prefix)
        return flattened
    
    def unflatten_record(self, flat_record: Dict[str, str]) -> Dict[str, Any]:
        """Unflatten a record from dot notation back to nested structure."""
        if not self.options.flatten_nested:
            return flat_record
        
        result = {}
        
        for key, value in flat_record.items():
            if self.options.nested_separator in key:
                parts = key.split(self.options.nested_separator)
                current = result
                
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                
                # Try to parse JSON strings back to lists
                if isinstance(value, str) and value.startswith('['):
                    try:
                        import json
                        current[parts[-1]] = json.loads(value)
                    except:
                        current[parts[-1]] = value
                else:
                    current[parts[-1]] = self._parse_value(value)
            else:
                result[key] = self._parse_value(value)
        
        return result
    
    def _parse_value(self, value: Any) -> Any:
        """Parse a value to its appropriate type."""
        if not self.options.preserve_types:
            return value

        # If not a string, return as-is
        if not isinstance(value, str):
            return value

        if value == "":
            return None

        # Try to parse as number
        try:
            if '.' in value:
                return float(value)
            return int(value)
        except ValueError:
            pass

        # Try to parse as boolean
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'

        # Return as string
        return value


class FormatDetector:
    """Detects file format from content and extension."""
    
    @staticmethod
    def detect_format(file_path: Path) -> FileFormat:
        """Detect the format of a file."""
        # First try by extension
        ext = file_path.suffix.lower()
        if ext == '.json':
            # Need to check if it's JSON array or JSONL
            return FormatDetector._detect_json_format(file_path)
        elif ext == '.jsonl' or ext == '.ndjson':
            return FileFormat.JSONL
        elif ext == '.csv':
            return FileFormat.CSV
        
        # Try to detect from content
        return FormatDetector._detect_from_content(file_path)
    
    @staticmethod
    def _detect_json_format(file_path: Path) -> FileFormat:
        """Detect if a .json file is JSON array or JSONL."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                first_char = f.read(1)
                if first_char == '[':
                    return FileFormat.JSON
                elif first_char == '{':
                    # Could be JSONL, check if there are multiple lines
                    f.seek(0)
                    lines = f.readlines()
                    if len(lines) > 1:
                        return FileFormat.JSONL
                    return FileFormat.JSON
        except:
            pass
        
        return FileFormat.UNKNOWN
    
    @staticmethod
    def _detect_from_content(file_path: Path) -> FileFormat:
        """Detect format from file content."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # Read first few lines
                lines = []
                for _ in range(5):
                    line = f.readline()
                    if not line:
                        break
                    lines.append(line.strip())
                
                if not lines:
                    return FileFormat.UNKNOWN
                
                # Try to parse as JSON
                try:
                    import json
                    # Check if first line is valid JSON
                    json.loads(lines[0])
                    # If we have multiple lines with JSON objects, it's JSONL
                    if len(lines) > 1:
                        json.loads(lines[1])
                        return FileFormat.JSONL
                    return FileFormat.JSON
                except:
                    pass
                
                # Check for CSV patterns
                if ',' in lines[0] or '\t' in lines[0]:
                    return FileFormat.CSV
                
        except:
            pass
        
        return FileFormat.UNKNOWN


class EncodingDetector:
    """Detects file encoding."""
    
    @staticmethod
    def detect_encoding(file_path: Path) -> str:
        """Detect the encoding of a file."""
        # Try common encodings
        encodings = ['utf-8', 'utf-16', 'latin-1', 'cp1252', 'ascii']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    # Try to read the entire file
                    f.read()
                return encoding
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        # Default to utf-8
        return 'utf-8'