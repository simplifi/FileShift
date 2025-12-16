"""
Tests for file split and merge operations.
"""
import pytest
import json
import csv
from pathlib import Path

from src.converters import (
    FileFormat, SplitOptions, MergeOptions,
    FileSplitter, FileMerger, get_file_info, count_records
)


class TestFileSplitter:
    """Tests for FileSplitter."""

    def test_split_by_num_files(self, large_jsonl_file, temp_dir):
        """Test splitting into a specific number of files."""
        split_options = SplitOptions(
            split_mode="by_files",
            num_files=4,
            output_format=FileFormat.JSONL,
            output_dir=temp_dir
        )

        splitter = FileSplitter(split_options)
        results = list(splitter.split(large_jsonl_file))

        # Should create 4 files
        assert len(results) == 4

        # Total records should match
        total_records = sum(count for _, count in results)
        assert total_records == 10000

        # Each file should have roughly equal records
        for _, count in results:
            assert 2400 <= count <= 2600

    def test_split_by_rows(self, large_jsonl_file, temp_dir):
        """Test splitting by number of rows per file."""
        split_options = SplitOptions(
            split_mode="by_rows",
            rows_per_file=3000,
            output_format=FileFormat.JSONL,
            output_dir=temp_dir
        )

        splitter = FileSplitter(split_options)
        results = list(splitter.split(large_jsonl_file))

        # Should create 4 files (3000 + 3000 + 3000 + 1000)
        assert len(results) == 4

        # First 3 files should have exactly 3000 records
        assert results[0][1] == 3000
        assert results[1][1] == 3000
        assert results[2][1] == 3000
        assert results[3][1] == 1000

    def test_split_by_size(self, large_jsonl_file, temp_dir):
        """Test splitting by approximate file size."""
        split_options = SplitOptions(
            split_mode="by_size",
            size_kb=100,  # 100 KB per file
            output_format=FileFormat.JSONL,
            output_dir=temp_dir
        )

        splitter = FileSplitter(split_options)
        results = list(splitter.split(large_jsonl_file))

        # Should create multiple files
        assert len(results) > 1

        # Total records should match
        total_records = sum(count for _, count in results)
        assert total_records == 10000

    def test_split_format_conversion_json_to_csv(self, sample_json_array_file, temp_dir):
        """Test splitting JSON into CSV files."""
        split_options = SplitOptions(
            split_mode="by_rows",
            rows_per_file=2,
            output_format=FileFormat.CSV,
            output_dir=temp_dir
        )

        splitter = FileSplitter(split_options)
        results = list(splitter.split(sample_json_array_file))

        # Should create 2 files (2 + 1)
        assert len(results) == 2

        # Verify output files are CSV
        for output_path, _ in results:
            assert output_path.suffix == '.csv'
            assert output_path.exists()

            # Verify CSV content
            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) > 0

    def test_split_format_conversion_csv_to_jsonl(self, sample_csv_file, temp_dir):
        """Test splitting CSV into JSONL files."""
        split_options = SplitOptions(
            split_mode="by_rows",
            rows_per_file=2,
            output_format=FileFormat.JSONL,
            output_dir=temp_dir
        )

        splitter = FileSplitter(split_options)
        results = list(splitter.split(sample_csv_file))

        # Should create 2 files
        assert len(results) == 2

        # Verify output files are JSONL
        for output_path, _ in results:
            assert output_path.suffix == '.jsonl'

    def test_split_empty_result_for_empty_file(self, temp_dir):
        """Test that splitting an empty file produces no output."""
        # Create empty file
        empty_file = temp_dir / "empty.jsonl"
        empty_file.touch()

        split_options = SplitOptions(
            split_mode="by_rows",
            rows_per_file=10,
            output_format=FileFormat.JSONL,
            output_dir=temp_dir
        )

        splitter = FileSplitter(split_options)
        results = list(splitter.split(empty_file))

        assert len(results) == 0


class TestFileMerger:
    """Tests for FileMerger."""

    def test_merge_same_schema(self, temp_dir):
        """Test merging files with identical schemas."""
        # Create two files with same schema
        file1 = temp_dir / "file1.jsonl"
        file2 = temp_dir / "file2.jsonl"

        with open(file1, 'w') as f:
            f.write(json.dumps({'id': 1, 'name': 'Alice'}) + '\n')
            f.write(json.dumps({'id': 2, 'name': 'Bob'}) + '\n')

        with open(file2, 'w') as f:
            f.write(json.dumps({'id': 3, 'name': 'Charlie'}) + '\n')
            f.write(json.dumps({'id': 4, 'name': 'David'}) + '\n')

        output_path = temp_dir / "merged.jsonl"
        merge_options = MergeOptions(
            output_format=FileFormat.JSONL,
            output_path=output_path,
            schema_strategy="union"
        )

        merger = FileMerger(merge_options)
        result_path, total_records = merger.merge([file1, file2])

        assert total_records == 4
        assert result_path == output_path

        # Verify merged content
        with open(output_path, 'r') as f:
            lines = f.readlines()
        assert len(lines) == 4

    def test_merge_different_schemas_union(self, temp_dir):
        """Test merging files with different schemas using union."""
        # File 1: fields a, b
        file1 = temp_dir / "file1.jsonl"
        with open(file1, 'w') as f:
            f.write(json.dumps({'a': 1, 'b': 2}) + '\n')

        # File 2: fields b, c
        file2 = temp_dir / "file2.jsonl"
        with open(file2, 'w') as f:
            f.write(json.dumps({'b': 3, 'c': 4}) + '\n')

        output_path = temp_dir / "merged.csv"
        merge_options = MergeOptions(
            output_format=FileFormat.CSV,
            output_path=output_path,
            schema_strategy="union"
        )

        merger = FileMerger(merge_options)
        result_path, total_records = merger.merge([file1, file2])

        assert total_records == 2

        # Verify CSV has all fields
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            fieldnames = reader.fieldnames

        # Should have a, b, c fields
        assert 'a' in fieldnames
        assert 'b' in fieldnames
        assert 'c' in fieldnames

    def test_merge_different_schemas_intersection(self, temp_dir):
        """Test merging files with different schemas using intersection."""
        # File 1: fields a, b, c
        file1 = temp_dir / "file1.jsonl"
        with open(file1, 'w') as f:
            f.write(json.dumps({'a': 1, 'b': 2, 'c': 3}) + '\n')

        # File 2: fields b, c, d
        file2 = temp_dir / "file2.jsonl"
        with open(file2, 'w') as f:
            f.write(json.dumps({'b': 4, 'c': 5, 'd': 6}) + '\n')

        output_path = temp_dir / "merged.csv"
        merge_options = MergeOptions(
            output_format=FileFormat.CSV,
            output_path=output_path,
            schema_strategy="intersection"
        )

        merger = FileMerger(merge_options)
        result_path, total_records = merger.merge([file1, file2])

        # Verify only common fields (b, c)
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames

        assert 'b' in fieldnames
        assert 'c' in fieldnames
        assert 'a' not in fieldnames
        assert 'd' not in fieldnames

    def test_merge_mixed_formats(self, sample_json_array_file, sample_csv_file, temp_dir):
        """Test merging JSON and CSV files together."""
        output_path = temp_dir / "merged.csv"
        merge_options = MergeOptions(
            output_format=FileFormat.CSV,
            output_path=output_path,
            schema_strategy="union"
        )

        merger = FileMerger(merge_options)
        result_path, total_records = merger.merge([sample_json_array_file, sample_csv_file])

        # Both files have 3 records
        assert total_records == 6

    def test_merge_preserves_all_records(self, temp_dir):
        """Test that no records are lost during merge."""
        # Create files with known record counts
        files = []
        total_expected = 0

        for i in range(5):
            file_path = temp_dir / f"file{i}.jsonl"
            record_count = (i + 1) * 10  # 10, 20, 30, 40, 50

            with open(file_path, 'w') as f:
                for j in range(record_count):
                    f.write(json.dumps({'id': j, 'source': i}) + '\n')

            files.append(file_path)
            total_expected += record_count

        output_path = temp_dir / "merged.jsonl"
        merge_options = MergeOptions(
            output_format=FileFormat.JSONL,
            output_path=output_path,
            schema_strategy="union"
        )

        merger = FileMerger(merge_options)
        result_path, total_records = merger.merge(files)

        assert total_records == total_expected  # 150 records

    def test_get_schema_preview(self, temp_dir):
        """Test schema preview functionality."""
        file1 = temp_dir / "file1.jsonl"
        file2 = temp_dir / "file2.jsonl"

        with open(file1, 'w') as f:
            f.write(json.dumps({'a': 1, 'b': 2}) + '\n')
            f.write(json.dumps({'a': 2, 'b': 3}) + '\n')

        with open(file2, 'w') as f:
            f.write(json.dumps({'b': 4, 'c': 5}) + '\n')

        merger = FileMerger(MergeOptions())
        preview = merger.get_schema_preview([file1, file2])

        assert preview['field_count'] == 3  # a, b, c
        assert preview['total_records'] == 3
        assert len(preview['file_info']) == 2


class TestUtilityFunctions:
    """Tests for utility functions."""

    def test_count_records_jsonl(self, sample_jsonl_file):
        """Test counting records in JSONL file."""
        count = count_records(sample_jsonl_file)
        assert count == 3

    def test_count_records_json(self, sample_json_array_file):
        """Test counting records in JSON file."""
        count = count_records(sample_json_array_file)
        assert count == 3

    def test_count_records_csv(self, sample_csv_file):
        """Test counting records in CSV file."""
        count = count_records(sample_csv_file)
        assert count == 3

    def test_get_file_info(self, sample_jsonl_file):
        """Test getting file info."""
        info = get_file_info(sample_jsonl_file)

        assert info['name'] == 'sample.jsonl'
        assert info['format'] == 'jsonl'
        assert info['record_count'] == 3
        assert info['field_count'] == 4
        assert 'name' in info['fields']
        assert 'size_kb' in info


class TestRoundTrip:
    """Tests for round-trip split and merge operations."""

    def test_split_and_merge_preserves_data(self, large_jsonl_file, temp_dir):
        """Test that split followed by merge preserves all data."""
        # Split the file
        split_options = SplitOptions(
            split_mode="by_files",
            num_files=5,
            output_format=FileFormat.JSONL,
            output_dir=temp_dir
        )

        splitter = FileSplitter(split_options)
        split_results = list(splitter.split(large_jsonl_file))
        split_files = [path for path, _ in split_results]

        # Merge the files back
        output_path = temp_dir / "merged.jsonl"
        merge_options = MergeOptions(
            output_format=FileFormat.JSONL,
            output_path=output_path,
            schema_strategy="union"
        )

        merger = FileMerger(merge_options)
        result_path, total_records = merger.merge(split_files)

        # Should have all 10000 records
        assert total_records == 10000
