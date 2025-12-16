# Format converters package
"""
FileShift converters package.

Provides format handlers for JSON, JSONL, and CSV files,
as well as split and merge operations.
"""

from .base import (
    FileFormat,
    ConversionOptions,
    FileMetadata,
    FormatHandler,
    FormatDetector,
    EncodingDetector,
)

from .handlers import (
    JSONHandler,
    JSONLHandler,
    CSVHandler,
    get_handler_for_format,
    get_handler_for_file,
)

from .operations import (
    SplitOptions,
    MergeOptions,
    FileSplitter,
    FileMerger,
    count_records,
    get_file_info,
)

__all__ = [
    # Base classes and types
    'FileFormat',
    'ConversionOptions',
    'FileMetadata',
    'FormatHandler',
    'FormatDetector',
    'EncodingDetector',
    # Format handlers
    'JSONHandler',
    'JSONLHandler',
    'CSVHandler',
    'get_handler_for_format',
    'get_handler_for_file',
    # Operations
    'SplitOptions',
    'MergeOptions',
    'FileSplitter',
    'FileMerger',
    'count_records',
    'get_file_info',
]
