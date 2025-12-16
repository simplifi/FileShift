"""
Tests for format handler implementations.
"""
import pytest
import json
import csv
from pathlib import Path

from src.converters import (
    FileFormat, ConversionOptions,
    JSONHandler, JSONLHandler, CSVHandler,
    get_handler_for_format, get_handler_for_file
)


class TestJSONHandler:
    """Tests for JSONHandler."""

    def test_can_handle_json_array(self, sample_json_array_file):
        """Test that handler can handle JSON array files."""
        handler = JSONHandler()
        assert handler.can_handle(sample_json_array_file) is True

    def test_cannot_handle_jsonl(self, sample_jsonl_file):
        """Test that handler rejects JSONL files."""
        handler = JSONHandler()
        assert handler.can_handle(sample_jsonl_file) is False

    def test_detect_metadata(self, sample_json_array_file):
        """Test metadata detection for JSON files."""
        handler = JSONHandler()
        metadata = handler.detect_metadata(sample_json_array_file)

        assert metadata.format == FileFormat.JSON
        assert metadata.estimated_records == 3
        assert 'name' in metadata.detected_fields
        assert 'age' in metadata.detected_fields
        assert len(metadata.sample_records) == 3

    def test_read_records(self, sample_json_array_file):
        """Test reading records from JSON file."""
        handler = JSONHandler()
        records = list(handler.read_records(sample_json_array_file))

        assert len(records) == 3
        assert records[0]['name'] == 'Alice'
        assert records[1]['name'] == 'Bob'
        assert records[2]['name'] == 'Charlie'

    def test_write_records(self, temp_dir):
        """Test writing records to JSON file."""
        handler = JSONHandler()
        records = [
            {'id': 1, 'name': 'Test1'},
            {'id': 2, 'name': 'Test2'},
        ]
        output_path = temp_dir / 'output.json'

        count = handler.write_records(iter(records), output_path)

        assert count == 2
        assert output_path.exists()

        # Verify written content
        with open(output_path, 'r') as f:
            data = json.load(f)
        assert len(data) == 2
        assert data[0]['name'] == 'Test1'


class TestJSONLHandler:
    """Tests for JSONLHandler."""

    def test_can_handle_jsonl(self, sample_jsonl_file):
        """Test that handler can handle JSONL files."""
        handler = JSONLHandler()
        assert handler.can_handle(sample_jsonl_file) is True

    def test_cannot_handle_json_array(self, sample_json_array_file):
        """Test that handler rejects JSON array files."""
        handler = JSONLHandler()
        assert handler.can_handle(sample_json_array_file) is False

    def test_detect_metadata(self, sample_jsonl_file):
        """Test metadata detection for JSONL files."""
        handler = JSONLHandler()
        metadata = handler.detect_metadata(sample_jsonl_file)

        assert metadata.format == FileFormat.JSONL
        assert metadata.estimated_records == 3
        assert 'name' in metadata.detected_fields
        assert 'city' in metadata.detected_fields

    def test_read_records_streaming(self, large_jsonl_file):
        """Test streaming read of large JSONL file."""
        handler = JSONLHandler()
        records = handler.read_records(large_jsonl_file)

        # Verify it's an iterator (streaming)
        assert hasattr(records, '__iter__')

        # Count records
        count = sum(1 for _ in records)
        assert count == 10000

    def test_write_records(self, temp_dir):
        """Test writing records to JSONL file."""
        handler = JSONLHandler()
        records = [
            {'id': 1, 'name': 'Test1'},
            {'id': 2, 'name': 'Test2'},
            {'id': 3, 'name': 'Test3'},
        ]
        output_path = temp_dir / 'output.jsonl'

        count = handler.write_records(iter(records), output_path)

        assert count == 3
        assert output_path.exists()

        # Verify written content
        with open(output_path, 'r') as f:
            lines = f.readlines()
        assert len(lines) == 3
        assert json.loads(lines[0])['name'] == 'Test1'


class TestCSVHandler:
    """Tests for CSVHandler."""

    def test_can_handle_csv(self, sample_csv_file):
        """Test that handler can handle CSV files."""
        handler = CSVHandler()
        assert handler.can_handle(sample_csv_file) is True

    def test_detect_metadata(self, sample_csv_file):
        """Test metadata detection for CSV files."""
        handler = CSVHandler()
        metadata = handler.detect_metadata(sample_csv_file)

        assert metadata.format == FileFormat.CSV
        assert metadata.estimated_records == 3
        assert 'name' in metadata.detected_fields
        assert 'id' in metadata.detected_fields

    def test_read_records(self, sample_csv_file):
        """Test reading records from CSV file."""
        handler = CSVHandler()
        records = list(handler.read_records(sample_csv_file))

        assert len(records) == 3
        assert records[0]['name'] == 'Alice'

    def test_write_records(self, temp_dir):
        """Test writing records to CSV file."""
        handler = CSVHandler()
        records = [
            {'id': 1, 'name': 'Test1', 'value': 100},
            {'id': 2, 'name': 'Test2', 'value': 200},
        ]
        output_path = temp_dir / 'output.csv'

        count = handler.write_records(iter(records), output_path)

        assert count == 2
        assert output_path.exists()

        # Verify written content
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 2
        assert rows[0]['name'] == 'Test1'


class TestHandlerFactory:
    """Tests for handler factory functions."""

    def test_get_handler_for_format_json(self):
        """Test getting JSON handler by format."""
        handler = get_handler_for_format(FileFormat.JSON)
        assert isinstance(handler, JSONHandler)

    def test_get_handler_for_format_jsonl(self):
        """Test getting JSONL handler by format."""
        handler = get_handler_for_format(FileFormat.JSONL)
        assert isinstance(handler, JSONLHandler)

    def test_get_handler_for_format_csv(self):
        """Test getting CSV handler by format."""
        handler = get_handler_for_format(FileFormat.CSV)
        assert isinstance(handler, CSVHandler)

    def test_get_handler_for_format_unknown(self):
        """Test error for unknown format."""
        with pytest.raises(ValueError):
            get_handler_for_format(FileFormat.UNKNOWN)

    def test_get_handler_for_file_json(self, sample_json_array_file):
        """Test auto-detecting handler for JSON file."""
        handler = get_handler_for_file(sample_json_array_file)
        assert isinstance(handler, JSONHandler)

    def test_get_handler_for_file_jsonl(self, sample_jsonl_file):
        """Test auto-detecting handler for JSONL file."""
        handler = get_handler_for_file(sample_jsonl_file)
        assert isinstance(handler, JSONLHandler)

    def test_get_handler_for_file_csv(self, sample_csv_file):
        """Test auto-detecting handler for CSV file."""
        handler = get_handler_for_file(sample_csv_file)
        assert isinstance(handler, CSVHandler)


class TestFormatConversion:
    """Tests for converting between formats."""

    def test_json_to_csv(self, sample_json_array_file, temp_dir):
        """Test converting JSON to CSV."""
        json_handler = JSONHandler()
        csv_handler = CSVHandler()

        records = json_handler.read_records(sample_json_array_file)
        output_path = temp_dir / 'converted.csv'
        count = csv_handler.write_records(records, output_path)

        assert count == 3
        assert output_path.exists()

        # Verify CSV content
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 3
        assert rows[0]['name'] == 'Alice'

    def test_jsonl_to_json(self, sample_jsonl_file, temp_dir):
        """Test converting JSONL to JSON."""
        jsonl_handler = JSONLHandler()
        json_handler = JSONHandler()

        records = jsonl_handler.read_records(sample_jsonl_file)
        output_path = temp_dir / 'converted.json'
        count = json_handler.write_records(records, output_path)

        assert count == 3

        # Verify JSON content
        with open(output_path, 'r') as f:
            data = json.load(f)
        assert len(data) == 3

    def test_csv_to_jsonl(self, sample_csv_file, temp_dir):
        """Test converting CSV to JSONL."""
        csv_handler = CSVHandler()
        jsonl_handler = JSONLHandler()

        records = csv_handler.read_records(sample_csv_file)
        output_path = temp_dir / 'converted.jsonl'
        count = jsonl_handler.write_records(records, output_path)

        assert count == 3

        # Verify JSONL content
        with open(output_path, 'r') as f:
            lines = f.readlines()
        assert len(lines) == 3
