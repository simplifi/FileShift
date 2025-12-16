"""
Tests for base classes and format detection.
"""
import pytest
from pathlib import Path
import json

from src.converters.base import (
    FileFormat, FormatDetector, EncodingDetector,
    ConversionOptions, FormatHandler
)


class TestFormatDetector:
    """Test format detection functionality."""
    
    def test_detect_json_array_format(self, sample_json_array_file):
        """Test detection of JSON array format."""
        detected = FormatDetector.detect_format(sample_json_array_file)
        assert detected == FileFormat.JSON
    
    def test_detect_jsonl_format(self, sample_jsonl_file):
        """Test detection of JSONL format."""
        detected = FormatDetector.detect_format(sample_jsonl_file)
        assert detected == FileFormat.JSONL
    
    def test_detect_csv_format(self, sample_csv_file):
        """Test detection of CSV format."""
        detected = FormatDetector.detect_format(sample_csv_file)
        assert detected == FileFormat.CSV
    
    def test_detect_jsonl_with_json_extension(self, temp_dir):
        """Test detection of JSONL format in .json file."""
        file_path = temp_dir / "test.json"
        with open(file_path, 'w') as f:
            f.write('{"id": 1}\n')
            f.write('{"id": 2}\n')
            f.write('{"id": 3}\n')
        
        detected = FormatDetector.detect_format(file_path)
        assert detected == FileFormat.JSONL
    
    def test_detect_unknown_format(self, temp_dir):
        """Test detection of unknown format."""
        file_path = temp_dir / "test.txt"
        with open(file_path, 'w') as f:
            f.write("This is not a data file\n")
        
        detected = FormatDetector.detect_format(file_path)
        assert detected == FileFormat.UNKNOWN


class TestEncodingDetector:
    """Test encoding detection functionality."""
    
    def test_detect_utf8_encoding(self, sample_json_array_file):
        """Test detection of UTF-8 encoding."""
        detected = EncodingDetector.detect_encoding(sample_json_array_file)
        assert detected == 'utf-8'
    
    def test_detect_latin1_encoding(self, mixed_encoding_file):
        """Test detection of Latin-1 encoding."""
        detected = EncodingDetector.detect_encoding(mixed_encoding_file)
        assert detected == 'latin-1'


class TestConversionOptions:
    """Test ConversionOptions dataclass."""
    
    def test_default_options(self):
        """Test default conversion options."""
        options = ConversionOptions()
        assert options.encoding == "utf-8"
        assert options.delimiter == ","
        assert options.flatten_nested == True
        assert options.nested_separator == "."
        assert options.preserve_types == True
    
    def test_custom_options(self):
        """Test custom conversion options."""
        options = ConversionOptions(
            encoding="latin-1",
            delimiter="|",
            nested_separator="_"
        )
        assert options.encoding == "latin-1"
        assert options.delimiter == "|"
        assert options.nested_separator == "_"


class TestFormatHandlerBase:
    """Test base FormatHandler functionality."""
    
    def test_extract_fields_flat(self):
        """Test field extraction from flat record."""
        handler = DummyHandler()
        record = {"id": 1, "name": "Test", "age": 30}
        fields = handler.extract_fields(record)
        
        assert fields == {"id", "name", "age"}
    
    def test_extract_fields_nested(self):
        """Test field extraction from nested record."""
        handler = DummyHandler()
        record = {
            "id": 1,
            "user": {
                "name": "Test",
                "contact": {
                    "email": "test@example.com"
                }
            }
        }
        fields = handler.extract_fields(record)
        
        expected = {"id", "user", "user.name", "user.contact", "user.contact.email"}
        assert fields == expected
    
    def test_flatten_record(self):
        """Test record flattening."""
        handler = DummyHandler()
        record = {
            "id": 1,
            "user": {
                "name": "Test",
                "contact": {
                    "email": "test@example.com",
                    "phone": "123-456"
                }
            },
            "tags": ["python", "data"]
        }
        
        flattened = handler.flatten_record(record)
        
        assert flattened["id"] == 1
        assert flattened["user.name"] == "Test"
        assert flattened["user.contact.email"] == "test@example.com"
        assert flattened["user.contact.phone"] == "123-456"
        assert json.loads(flattened["tags"]) == ["python", "data"]
    
    def test_unflatten_record(self):
        """Test record unflattening."""
        handler = DummyHandler()
        flat_record = {
            "id": "1",
            "user.name": "Test",
            "user.contact.email": "test@example.com",
            "tags": '["python", "data"]'
        }
        
        unflattened = handler.unflatten_record(flat_record)
        
        assert unflattened["id"] == 1
        assert unflattened["user"]["name"] == "Test"
        assert unflattened["user"]["contact"]["email"] == "test@example.com"
        assert unflattened["tags"] == ["python", "data"]
    
    def test_parse_value_types(self):
        """Test value type parsing."""
        handler = DummyHandler()
        
        assert handler._parse_value("123") == 123
        assert handler._parse_value("123.45") == 123.45
        assert handler._parse_value("true") == True
        assert handler._parse_value("false") == False
        assert handler._parse_value("hello") == "hello"
        assert handler._parse_value("") is None


# Dummy implementation for testing base functionality
class DummyHandler(FormatHandler):
    """Dummy handler for testing base class functionality."""
    
    def can_handle(self, file_path: Path) -> bool:
        return True
    
    def detect_metadata(self, file_path: Path):
        return None
    
    def read_records(self, file_path: Path):
        yield {}
    
    def write_records(self, records, output_path: Path):
        return 0