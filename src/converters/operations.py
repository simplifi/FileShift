"""
File split and merge operations.
"""
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator, Dict, Any, List, Tuple, Optional, Set, Literal

from .base import FileFormat, ConversionOptions, FormatDetector
from .handlers import get_handler_for_format, get_handler_for_file


@dataclass
class SplitOptions:
    """Options for file split operations."""
    split_mode: Literal["by_files", "by_rows", "by_size"]
    num_files: Optional[int] = None       # For by_files mode
    rows_per_file: Optional[int] = None   # For by_rows mode
    size_kb: Optional[int] = None         # For by_size mode
    output_format: FileFormat = FileFormat.CSV
    output_dir: Optional[Path] = None
    filename_pattern: str = "{stem}_{num:03d}{ext}"


@dataclass
class MergeOptions:
    """Options for file merge operations."""
    output_format: FileFormat = FileFormat.CSV
    output_path: Optional[Path] = None
    schema_strategy: Literal["union", "intersection", "first_file"] = "union"


class FileSplitter:
    """Handles splitting a single file into multiple files."""

    def __init__(
        self,
        split_options: SplitOptions,
        conversion_options: Optional[ConversionOptions] = None
    ):
        self.split_options = split_options
        self.conversion_options = conversion_options or ConversionOptions()

    def split(self, input_path: Path) -> Iterator[Tuple[Path, int]]:
        """
        Split a file into multiple output files.

        Yields tuples of (output_path, record_count) for each created file.
        """
        input_path = Path(input_path)

        # Validate options
        if self.split_options.output_dir is None:
            self.split_options.output_dir = input_path.parent

        output_dir = Path(self.split_options.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Get input handler
        input_handler = get_handler_for_file(input_path, self.conversion_options)

        # Get output handler
        output_handler = get_handler_for_format(
            self.split_options.output_format,
            self.conversion_options
        )

        # Get file extension for output
        ext_map = {
            FileFormat.JSON: '.json',
            FileFormat.JSONL: '.jsonl',
            FileFormat.CSV: '.csv',
        }
        output_ext = ext_map.get(self.split_options.output_format, '.csv')

        # Split based on mode
        if self.split_options.split_mode == "by_files":
            yield from self._split_by_files(
                input_path, input_handler, output_handler, output_dir, output_ext
            )
        elif self.split_options.split_mode == "by_rows":
            yield from self._split_by_rows(
                input_path, input_handler, output_handler, output_dir, output_ext
            )
        elif self.split_options.split_mode == "by_size":
            yield from self._split_by_size(
                input_path, input_handler, output_handler, output_dir, output_ext
            )
        else:
            raise ValueError(f"Unknown split mode: {self.split_options.split_mode}")

    def _split_by_files(
        self,
        input_path: Path,
        input_handler,
        output_handler,
        output_dir: Path,
        output_ext: str
    ) -> Iterator[Tuple[Path, int]]:
        """Split into a specific number of files."""
        num_files = self.split_options.num_files or 2

        # First pass: count total records
        total_records = 0
        for _ in input_handler.read_records(input_path):
            total_records += 1

        if total_records == 0:
            return

        # Calculate records per file
        records_per_file = math.ceil(total_records / num_files)

        # Second pass: split records
        yield from self._write_chunks(
            input_path, input_handler, output_handler, output_dir, output_ext,
            records_per_file
        )

    def _split_by_rows(
        self,
        input_path: Path,
        input_handler,
        output_handler,
        output_dir: Path,
        output_ext: str
    ) -> Iterator[Tuple[Path, int]]:
        """Split by number of rows per file."""
        rows_per_file = self.split_options.rows_per_file or 1000

        yield from self._write_chunks(
            input_path, input_handler, output_handler, output_dir, output_ext,
            rows_per_file
        )

    def _split_by_size(
        self,
        input_path: Path,
        input_handler,
        output_handler,
        output_dir: Path,
        output_ext: str
    ) -> Iterator[Tuple[Path, int]]:
        """Split by approximate file size in KB."""
        size_kb = self.split_options.size_kb or 1000
        target_bytes = size_kb * 1024

        stem = input_path.stem
        file_num = 1
        current_records: List[Dict[str, Any]] = []
        current_size = 0

        for record in input_handler.read_records(input_path):
            # Estimate record size
            record_size = self._estimate_record_size(
                record,
                self.split_options.output_format
            )

            # Check if adding this record would exceed target size
            if current_size + record_size > target_bytes and current_records:
                # Write current chunk
                output_path = output_dir / self.split_options.filename_pattern.format(
                    stem=stem, num=file_num, ext=output_ext
                )
                count = output_handler.write_records(iter(current_records), output_path)
                yield output_path, count

                file_num += 1
                current_records = []
                current_size = 0

            current_records.append(record)
            current_size += record_size

        # Write remaining records
        if current_records:
            output_path = output_dir / self.split_options.filename_pattern.format(
                stem=stem, num=file_num, ext=output_ext
            )
            count = output_handler.write_records(iter(current_records), output_path)
            yield output_path, count

    def _write_chunks(
        self,
        input_path: Path,
        input_handler,
        output_handler,
        output_dir: Path,
        output_ext: str,
        records_per_file: int
    ) -> Iterator[Tuple[Path, int]]:
        """Write records in chunks of specified size."""
        stem = input_path.stem
        file_num = 1
        current_records: List[Dict[str, Any]] = []

        for record in input_handler.read_records(input_path):
            current_records.append(record)

            if len(current_records) >= records_per_file:
                # Write current chunk
                output_path = output_dir / self.split_options.filename_pattern.format(
                    stem=stem, num=file_num, ext=output_ext
                )
                count = output_handler.write_records(iter(current_records), output_path)
                yield output_path, count

                file_num += 1
                current_records = []

        # Write remaining records
        if current_records:
            output_path = output_dir / self.split_options.filename_pattern.format(
                stem=stem, num=file_num, ext=output_ext
            )
            count = output_handler.write_records(iter(current_records), output_path)
            yield output_path, count

    def _estimate_record_size(self, record: Dict[str, Any], output_format: FileFormat) -> int:
        """Estimate the size of a record in the output format."""
        import json

        if output_format == FileFormat.CSV:
            # Rough estimate: sum of string values + delimiters
            size = sum(len(str(v)) for v in record.values())
            size += len(record)  # Delimiters
            return size
        elif output_format == FileFormat.JSONL:
            return len(json.dumps(record)) + 1  # +1 for newline
        elif output_format == FileFormat.JSON:
            # JSON array format has more overhead
            return len(json.dumps(record)) + 3  # Rough estimate
        else:
            return len(json.dumps(record))


class FileMerger:
    """Handles merging multiple files into one."""

    def __init__(
        self,
        merge_options: MergeOptions,
        conversion_options: Optional[ConversionOptions] = None
    ):
        self.merge_options = merge_options
        self.conversion_options = conversion_options or ConversionOptions()

    def merge(self, input_paths: List[Path]) -> Tuple[Path, int]:
        """
        Merge multiple files into one.

        Returns tuple of (output_path, total_records).
        """
        if not input_paths:
            raise ValueError("No input files provided")

        input_paths = [Path(p) for p in input_paths]

        # Validate output path
        if self.merge_options.output_path is None:
            ext_map = {
                FileFormat.JSON: '.json',
                FileFormat.JSONL: '.jsonl',
                FileFormat.CSV: '.csv',
            }
            output_ext = ext_map.get(self.merge_options.output_format, '.csv')
            self.merge_options.output_path = input_paths[0].parent / f"merged{output_ext}"

        output_path = Path(self.merge_options.output_path)

        # Collect schema based on strategy
        all_fields = self._collect_schema(input_paths)

        # Get output handler
        output_handler = get_handler_for_format(
            self.merge_options.output_format,
            self.conversion_options
        )

        # Create record generator that reads from all files
        def all_records() -> Iterator[Dict[str, Any]]:
            for file_path in input_paths:
                handler = get_handler_for_file(file_path, self.conversion_options)
                for record in handler.read_records(file_path):
                    # Ensure record has all fields (for consistent output)
                    normalized = {}
                    for field in all_fields:
                        normalized[field] = record.get(field)
                    yield normalized

        # Write merged output
        total_records = output_handler.write_records(all_records(), output_path)

        return output_path, total_records

    def _collect_schema(self, input_paths: List[Path]) -> List[str]:
        """Collect field schema from input files based on strategy."""
        if self.merge_options.schema_strategy == "first_file":
            return self._get_fields_from_file(input_paths[0])

        elif self.merge_options.schema_strategy == "intersection":
            # Start with first file's fields, then intersect with others
            common_fields: Optional[Set[str]] = None

            for file_path in input_paths:
                fields = set(self._get_fields_from_file(file_path))
                if common_fields is None:
                    common_fields = fields
                else:
                    common_fields &= fields

            return sorted(common_fields or set())

        else:  # "union" (default)
            # Preserve order of first occurrence
            all_fields: List[str] = []
            seen: Set[str] = set()

            for file_path in input_paths:
                fields = self._get_fields_from_file(file_path)
                for field in fields:
                    if field not in seen:
                        all_fields.append(field)
                        seen.add(field)

            return all_fields

    def _get_fields_from_file(self, file_path: Path) -> List[str]:
        """Get field names from a single file."""
        handler = get_handler_for_file(file_path, self.conversion_options)
        metadata = handler.detect_metadata(file_path)
        return sorted(metadata.detected_fields)

    def get_schema_preview(self, input_paths: List[Path]) -> Dict[str, Any]:
        """
        Get a preview of the merge schema.

        Returns dict with:
        - 'fields': List of field names
        - 'field_count': Number of fields
        - 'total_records': Estimated total records
        - 'file_info': List of dicts with per-file info
        """
        input_paths = [Path(p) for p in input_paths]

        # Collect per-file info
        file_info = []
        total_records = 0

        for file_path in input_paths:
            handler = get_handler_for_file(file_path, self.conversion_options)
            metadata = handler.detect_metadata(file_path)

            file_info.append({
                'path': str(file_path),
                'name': file_path.name,
                'format': metadata.format.value,
                'record_count': metadata.estimated_records,
                'field_count': len(metadata.detected_fields),
                'fields': sorted(metadata.detected_fields)
            })
            total_records += metadata.estimated_records

        # Get merged fields
        fields = self._collect_schema(input_paths)

        return {
            'fields': fields,
            'field_count': len(fields),
            'total_records': total_records,
            'file_info': file_info
        }


def count_records(file_path: Path, options: Optional[ConversionOptions] = None) -> int:
    """Count the number of records in a file."""
    handler = get_handler_for_file(Path(file_path), options)
    metadata = handler.detect_metadata(Path(file_path))
    return metadata.estimated_records


def get_file_info(file_path: Path, options: Optional[ConversionOptions] = None) -> Dict[str, Any]:
    """Get detailed information about a file."""
    file_path = Path(file_path)
    handler = get_handler_for_file(file_path, options)
    metadata = handler.detect_metadata(file_path)

    return {
        'path': str(file_path),
        'name': file_path.name,
        'format': metadata.format.value,
        'encoding': metadata.encoding,
        'size_bytes': metadata.size_bytes,
        'size_kb': round(metadata.size_bytes / 1024, 2),
        'record_count': metadata.estimated_records,
        'field_count': len(metadata.detected_fields),
        'fields': sorted(metadata.detected_fields),
        'sample_records': metadata.sample_records[:3]
    }
