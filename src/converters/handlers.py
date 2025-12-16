"""
Concrete format handler implementations for JSON, JSONL, and CSV files.
"""
import csv
import json
from pathlib import Path
from typing import Iterator, Dict, Any, List, Set, Optional

from .base import (
    FormatHandler, FileFormat, FileMetadata, ConversionOptions,
    FormatDetector, EncodingDetector
)


class JSONHandler(FormatHandler):
    """Handler for JSON array files."""

    def can_handle(self, file_path: Path) -> bool:
        """Check if this handler can process the given file."""
        if file_path.suffix.lower() == '.json':
            detected = FormatDetector.detect_format(file_path)
            return detected == FileFormat.JSON
        return False

    def detect_metadata(self, file_path: Path) -> FileMetadata:
        """Detect and return metadata about the file."""
        encoding = EncodingDetector.detect_encoding(file_path)
        size_bytes = file_path.stat().st_size

        # Detect line ending
        with open(file_path, 'rb') as f:
            sample = f.read(8192)
            if b'\r\n' in sample:
                line_ending = '\r\n'
            elif b'\r' in sample:
                line_ending = '\r'
            else:
                line_ending = '\n'

        # Read and analyze content
        detected_fields: Set[str] = set()
        sample_records: List[Dict[str, Any]] = []
        estimated_records = 0

        try:
            with open(file_path, 'r', encoding=encoding) as f:
                data = json.load(f)
                if isinstance(data, list):
                    estimated_records = len(data)
                    for i, record in enumerate(data):
                        if isinstance(record, dict):
                            detected_fields.update(self.extract_fields(record))
                            if i < 5:
                                sample_records.append(record)
                elif isinstance(data, dict):
                    estimated_records = 1
                    detected_fields.update(self.extract_fields(data))
                    sample_records.append(data)
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass

        return FileMetadata(
            format=FileFormat.JSON,
            encoding=encoding,
            line_ending=line_ending,
            size_bytes=size_bytes,
            estimated_records=estimated_records,
            detected_fields=detected_fields,
            sample_records=sample_records
        )

    def read_records(self, file_path: Path) -> Iterator[Dict[str, Any]]:
        """Read records from the file as an iterator."""
        encoding = EncodingDetector.detect_encoding(file_path)

        with open(file_path, 'r', encoding=encoding) as f:
            data = json.load(f)

            if isinstance(data, list):
                for record in data:
                    if isinstance(record, dict):
                        if self.options.flatten_nested:
                            yield self.flatten_record(record)
                        else:
                            yield record
            elif isinstance(data, dict):
                if self.options.flatten_nested:
                    yield self.flatten_record(data)
                else:
                    yield data

    def write_records(self, records: Iterator[Dict[str, Any]], output_path: Path) -> int:
        """Write records to the output file. Returns number of records written."""
        records_list = []
        count = 0

        for record in records:
            if self.options.flatten_nested:
                # Unflatten for JSON output
                records_list.append(self.unflatten_record(record))
            else:
                records_list.append(record)
            count += 1

        with open(output_path, 'w', encoding=self.options.encoding) as f:
            json.dump(records_list, f, indent=2, ensure_ascii=False)

        return count


class JSONLHandler(FormatHandler):
    """Handler for JSONL (newline-delimited JSON) files."""

    def can_handle(self, file_path: Path) -> bool:
        """Check if this handler can process the given file."""
        suffix = file_path.suffix.lower()
        if suffix in ('.jsonl', '.ndjson'):
            return True
        if suffix == '.json':
            detected = FormatDetector.detect_format(file_path)
            return detected == FileFormat.JSONL
        return False

    def detect_metadata(self, file_path: Path) -> FileMetadata:
        """Detect and return metadata about the file."""
        encoding = EncodingDetector.detect_encoding(file_path)
        size_bytes = file_path.stat().st_size

        # Detect line ending
        with open(file_path, 'rb') as f:
            sample = f.read(8192)
            if b'\r\n' in sample:
                line_ending = '\r\n'
            elif b'\r' in sample:
                line_ending = '\r'
            else:
                line_ending = '\n'

        # Count records and collect fields (streaming)
        detected_fields: Set[str] = set()
        sample_records: List[Dict[str, Any]] = []
        estimated_records = 0

        try:
            with open(file_path, 'r', encoding=encoding) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                        if isinstance(record, dict):
                            estimated_records += 1
                            detected_fields.update(self.extract_fields(record))
                            if len(sample_records) < 5:
                                sample_records.append(record)
                    except json.JSONDecodeError:
                        if not self.options.skip_errors:
                            raise
        except UnicodeDecodeError:
            pass

        return FileMetadata(
            format=FileFormat.JSONL,
            encoding=encoding,
            line_ending=line_ending,
            size_bytes=size_bytes,
            estimated_records=estimated_records,
            detected_fields=detected_fields,
            sample_records=sample_records
        )

    def read_records(self, file_path: Path) -> Iterator[Dict[str, Any]]:
        """Read records from the file as an iterator (streaming)."""
        encoding = EncodingDetector.detect_encoding(file_path)

        with open(file_path, 'r', encoding=encoding) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    if isinstance(record, dict):
                        if self.options.flatten_nested:
                            yield self.flatten_record(record)
                        else:
                            yield record
                except json.JSONDecodeError:
                    if not self.options.skip_errors:
                        raise

    def write_records(self, records: Iterator[Dict[str, Any]], output_path: Path) -> int:
        """Write records to the output file. Returns number of records written."""
        count = 0

        with open(output_path, 'w', encoding=self.options.encoding) as f:
            for record in records:
                if self.options.flatten_nested:
                    # Unflatten for JSONL output
                    output_record = self.unflatten_record(record)
                else:
                    output_record = record
                f.write(json.dumps(output_record, ensure_ascii=False) + '\n')
                count += 1

        return count


class CSVHandler(FormatHandler):
    """Handler for CSV files."""

    def can_handle(self, file_path: Path) -> bool:
        """Check if this handler can process the given file."""
        if file_path.suffix.lower() == '.csv':
            return True
        detected = FormatDetector.detect_format(file_path)
        return detected == FileFormat.CSV

    def detect_metadata(self, file_path: Path) -> FileMetadata:
        """Detect and return metadata about the file."""
        encoding = EncodingDetector.detect_encoding(file_path)
        size_bytes = file_path.stat().st_size

        # Detect line ending
        with open(file_path, 'rb') as f:
            sample = f.read(8192)
            if b'\r\n' in sample:
                line_ending = '\r\n'
            elif b'\r' in sample:
                line_ending = '\r'
            else:
                line_ending = '\n'

        # Read and analyze content
        detected_fields: Set[str] = set()
        sample_records: List[Dict[str, Any]] = []
        estimated_records = 0

        try:
            with open(file_path, 'r', encoding=encoding, newline='') as f:
                # Try to detect delimiter
                sample_text = f.read(4096)
                f.seek(0)

                try:
                    dialect = csv.Sniffer().sniff(sample_text)
                    delimiter = dialect.delimiter
                except csv.Error:
                    delimiter = self.options.delimiter

                reader = csv.DictReader(f, delimiter=delimiter)

                for i, row in enumerate(reader):
                    estimated_records += 1
                    if i == 0:
                        # Get field names from header
                        detected_fields.update(row.keys())
                    if i < 5:
                        # Parse values for sample records
                        parsed_row = {}
                        for key, value in row.items():
                            if value is not None:
                                parsed_row[key] = self._parse_value(value)
                            else:
                                parsed_row[key] = None
                        sample_records.append(parsed_row)
        except (csv.Error, UnicodeDecodeError):
            pass

        return FileMetadata(
            format=FileFormat.CSV,
            encoding=encoding,
            line_ending=line_ending,
            size_bytes=size_bytes,
            estimated_records=estimated_records,
            detected_fields=detected_fields,
            sample_records=sample_records
        )

    def read_records(self, file_path: Path) -> Iterator[Dict[str, Any]]:
        """Read records from the file as an iterator."""
        encoding = EncodingDetector.detect_encoding(file_path)

        with open(file_path, 'r', encoding=encoding, newline='') as f:
            # Try to detect delimiter
            sample_text = f.read(4096)
            f.seek(0)

            try:
                dialect = csv.Sniffer().sniff(sample_text)
                delimiter = dialect.delimiter
            except csv.Error:
                delimiter = self.options.delimiter

            reader = csv.DictReader(f, delimiter=delimiter)

            for row in reader:
                # Parse values
                parsed_row = {}
                for key, value in row.items():
                    if value is not None and value != '':
                        parsed_row[key] = self._parse_value(value)
                    else:
                        parsed_row[key] = None if self.options.preserve_types else ''

                yield parsed_row

    def write_records(self, records: Iterator[Dict[str, Any]], output_path: Path) -> int:
        """Write records to the output file. Returns number of records written."""
        count = 0
        fieldnames: Optional[List[str]] = None
        writer: Optional[csv.DictWriter] = None

        with open(output_path, 'w', encoding=self.options.encoding, newline='') as f:
            for record in records:
                # Flatten nested structures for CSV
                if self.options.flatten_nested:
                    flat_record = self.flatten_record(record)
                else:
                    flat_record = record

                # Convert non-string values to strings
                row = {}
                for key, value in flat_record.items():
                    if value is None:
                        row[key] = ''
                    elif isinstance(value, (list, dict)):
                        row[key] = json.dumps(value)
                    else:
                        row[key] = str(value)

                # Initialize writer with first record's fields
                if writer is None:
                    fieldnames = list(row.keys())
                    writer = csv.DictWriter(
                        f,
                        fieldnames=fieldnames,
                        delimiter=self.options.delimiter,
                        quotechar=self.options.quotechar,
                        extrasaction='ignore'
                    )
                    writer.writeheader()

                # Ensure row has all fieldnames
                for field in fieldnames:
                    if field not in row:
                        row[field] = ''

                writer.writerow(row)
                count += 1

        return count

    def write_records_with_fields(
        self,
        records: Iterator[Dict[str, Any]],
        output_path: Path,
        fieldnames: List[str]
    ) -> int:
        """Write records with predefined field names (for merge operations)."""
        count = 0

        with open(output_path, 'w', encoding=self.options.encoding, newline='') as f:
            writer = csv.DictWriter(
                f,
                fieldnames=fieldnames,
                delimiter=self.options.delimiter,
                quotechar=self.options.quotechar,
                extrasaction='ignore'
            )
            writer.writeheader()

            for record in records:
                # Flatten if needed
                if self.options.flatten_nested:
                    flat_record = self.flatten_record(record)
                else:
                    flat_record = record

                # Convert values to strings
                row = {}
                for field in fieldnames:
                    value = flat_record.get(field)
                    if value is None:
                        row[field] = ''
                    elif isinstance(value, (list, dict)):
                        row[field] = json.dumps(value)
                    else:
                        row[field] = str(value)

                writer.writerow(row)
                count += 1

        return count


def get_handler_for_format(
    file_format: FileFormat,
    options: Optional[ConversionOptions] = None
) -> FormatHandler:
    """Get the appropriate handler for a file format."""
    handlers = {
        FileFormat.JSON: JSONHandler,
        FileFormat.JSONL: JSONLHandler,
        FileFormat.CSV: CSVHandler,
    }

    handler_class = handlers.get(file_format)
    if handler_class is None:
        raise ValueError(f"No handler available for format: {file_format}")

    return handler_class(options)


def get_handler_for_file(
    file_path: Path,
    options: Optional[ConversionOptions] = None
) -> FormatHandler:
    """Auto-detect format and return appropriate handler."""
    file_format = FormatDetector.detect_format(file_path)

    if file_format == FileFormat.UNKNOWN:
        raise ValueError(f"Unable to detect format for file: {file_path}")

    return get_handler_for_format(file_format, options)
