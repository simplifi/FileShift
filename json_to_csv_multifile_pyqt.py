#!/usr/bin/env python3
"""
FileShift - File Converter (Multi-File) - PyQt6 Version
GUI tool for converting, splitting, and merging JSON, JSONL, and CSV files
"""

import sys
import json
import csv
import os
from pathlib import Path
from collections import Counter
from datetime import datetime
from typing import List, Optional, Dict, Any

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QGroupBox, QPushButton, QTextEdit,
    QLabel, QRadioButton, QComboBox, QFileDialog,
    QMessageBox, QButtonGroup, QTabWidget, QSpinBox,
    QLineEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

# Import converters
from src.converters import (
    FileFormat, ConversionOptions, SplitOptions, MergeOptions,
    FileSplitter, FileMerger, get_handler_for_file, get_file_info
)


# Button style constants
GREEN_BUTTON_STYLE = """
    QPushButton {
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
        padding: 8px;
        border: none;
        border-radius: 4px;
    }
    QPushButton:hover {
        background-color: #45a049;
    }
    QPushButton:disabled {
        background-color: #cccccc;
    }
"""

FILE_FILTER = "Data Files (*.json *.jsonl *.csv);;JSON Files (*.json);;JSONL Files (*.jsonl);;CSV Files (*.csv);;All Files (*.*)"


class SchemaAnalyzerThread(QThread):
    """Background thread for schema analysis"""
    progress = pyqtSignal(str)
    finished = pyqtSignal(dict, dict, set, dict, int)

    def __init__(self, file_paths):
        super().__init__()
        self.file_paths = file_paths

    def run(self):
        file_schemas = {}
        all_fields = set()
        field_frequency = Counter()
        total_records = 0

        self.progress.emit("Analyzing file schemas...")

        for file_path in self.file_paths:
            fields_set = set()
            record_count = 0

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            try:
                                data = json.loads(line)
                                record_count += 1
                                self.extract_fields(data, fields_set)
                            except json.JSONDecodeError:
                                continue
            except Exception:
                continue

            file_schemas[file_path] = sorted(list(fields_set))
            all_fields.update(fields_set)
            total_records += record_count

            for field in fields_set:
                field_frequency[field] += 1

        self.finished.emit(file_schemas, dict(field_frequency), all_fields, file_schemas, total_records)

    def extract_fields(self, obj, fields_set, prefix=""):
        """Recursively extract field paths"""
        if isinstance(obj, dict):
            for key, value in obj.items():
                field_path = f"{prefix}.{key}" if prefix else key
                fields_set.add(field_path)
                if isinstance(value, dict):
                    self.extract_fields(value, fields_set, field_path)


class ConversionThread(QThread):
    """Background thread for file conversion"""
    progress = pyqtSignal(str)
    file_complete = pyqtSignal(str, int)
    finished = pyqtSignal(int, int)

    def __init__(self, file_paths, strategy, selected_fields, output_dir, file_schemas, all_fields):
        super().__init__()
        self.file_paths = file_paths
        self.strategy = strategy
        self.selected_fields = selected_fields
        self.output_dir = output_dir
        self.file_schemas = file_schemas
        self.all_fields = all_fields

    def run(self):
        total_records = 0

        for file_path in self.file_paths:
            self.progress.emit(f"Converting {Path(file_path).name}...")

            # Get fields based on strategy
            if self.strategy == "separate":
                fields = self.file_schemas.get(file_path, [])
            else:
                fields = sorted(list(self.all_fields))

            # Convert file
            records = self.convert_single_file(file_path, fields)
            total_records += records

            self.file_complete.emit(Path(file_path).name, records)

        self.finished.emit(len(self.file_paths), total_records)

    def convert_single_file(self, file_path, fields):
        """Convert a single file"""
        input_name = Path(file_path).stem
        output_file = os.path.join(self.output_dir, f"{input_name}.csv")

        records_written = 0
        with open(file_path, 'r', encoding='utf-8') as infile, \
             open(output_file, 'w', newline='', encoding='utf-8') as outfile:

            writer = csv.DictWriter(outfile, fieldnames=fields)
            writer.writeheader()

            for line in infile:
                if line.strip():
                    try:
                        data = json.loads(line)
                        row = {}
                        for field in fields:
                            row[field] = self.get_nested_value(data, field)
                        writer.writerow(row)
                        records_written += 1
                    except json.JSONDecodeError:
                        continue

        return records_written

    def get_nested_value(self, data, field_path):
        """Extract nested value"""
        keys = field_path.split('.')
        value = data
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return ""

        if isinstance(value, (list, dict)):
            return json.dumps(value)
        return value if value is not None else ""


class SplitThread(QThread):
    """Background thread for file splitting"""
    progress = pyqtSignal(str)
    file_created = pyqtSignal(str, int)
    finished = pyqtSignal(int, int)
    error = pyqtSignal(str)

    def __init__(self, input_path: Path, split_options: SplitOptions):
        super().__init__()
        self.input_path = input_path
        self.split_options = split_options

    def run(self):
        try:
            splitter = FileSplitter(self.split_options)
            total_files = 0
            total_records = 0

            self.progress.emit(f"Splitting {self.input_path.name}...")

            for output_path, record_count in splitter.split(self.input_path):
                total_files += 1
                total_records += record_count
                self.file_created.emit(output_path.name, record_count)
                self.progress.emit(f"Created {output_path.name} ({record_count:,} records)")

            self.finished.emit(total_files, total_records)
        except Exception as e:
            self.error.emit(str(e))


class MergeThread(QThread):
    """Background thread for file merging"""
    progress = pyqtSignal(str)
    file_processed = pyqtSignal(str)
    finished = pyqtSignal(str, int)
    error = pyqtSignal(str)

    def __init__(self, input_paths: List[Path], merge_options: MergeOptions):
        super().__init__()
        self.input_paths = input_paths
        self.merge_options = merge_options

    def run(self):
        try:
            merger = FileMerger(self.merge_options)

            self.progress.emit("Merging files...")

            output_path, total_records = merger.merge(self.input_paths)

            self.finished.emit(str(output_path), total_records)
        except Exception as e:
            self.error.emit(str(e))


class MultiFileConverter(QMainWindow):
    def __init__(self):
        super().__init__()
        self.selected_files = []
        self.file_schemas = {}
        self.all_fields = set()
        self.field_frequency = {}
        self.selected_strategy = "separate"

        # Split tab state
        self.split_input_file: Optional[Path] = None

        # Merge tab state
        self.merge_input_files: List[Path] = []

        self.init_ui()

    def init_ui(self):
        """Initialize the UI"""
        self.setWindowTitle("FileShift - File Converter")
        self.setGeometry(100, 100, 1200, 850)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title_label = QLabel("FileShift - File Converter")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)

        # Shared File Selection Section (at the top)
        self.setup_file_selection(main_layout)

        # Tab Widget (below file selection)
        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(self.create_convert_tab(), "Convert")
        self.tab_widget.addTab(self.create_split_tab(), "Split")
        self.tab_widget.addTab(self.create_merge_tab(), "Merge")
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        main_layout.addWidget(self.tab_widget)

        # Status Log (shared across tabs)
        self.setup_status_log(main_layout)

    def create_convert_tab(self) -> QWidget:
        """Create the Convert tab content"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)

        # Step 1: Schema Analysis
        step2_group = QGroupBox("Step 1: Schema Analysis")
        step2_layout = QVBoxLayout()

        self.analysis_label = QLabel("Select files to analyze schemas")
        self.analysis_label.setStyleSheet("color: #666666;")
        step2_layout.addWidget(self.analysis_label)

        step2_group.setLayout(step2_layout)
        layout.addWidget(step2_group)

        # Step 2: Field Selection
        step3_group = QGroupBox("Step 2: Field Selection")
        step3_layout = QVBoxLayout()

        self.step3_group = step3_group
        self.step3_group.setEnabled(False)

        desc_label = QLabel("Files have different schemas. Choose field selection strategy:")
        step3_layout.addWidget(desc_label)

        self.button_group = QButtonGroup()
        self.strategy_buttons = []

        strategies = [
            ("smart_auto", "Merge with Smart Auto - Fields in 70%+ of files (0 fields)"),
            ("all_available", "Merge with All Available - Union of all fields (0 fields)"),
            ("common_only", "Merge with Common Only - Fields in ALL files (0 fields)"),
            ("most_complete", "Merge with Most Complete File - Use 'file.json' (0 fields)"),
            ("separate", "Keep Files Separate - Individual CSVs with own fields")
        ]

        for i, (value, text) in enumerate(strategies):
            radio = QRadioButton(text)
            if value == "separate":
                radio.setChecked(True)
            radio.toggled.connect(lambda checked, v=value: self.strategy_changed(v) if checked else None)
            self.button_group.addButton(radio, i)
            self.strategy_buttons.append((value, radio))
            step3_layout.addWidget(radio)

        # Strategy dropdown
        dropdown_layout = QHBoxLayout()
        dropdown_label = QLabel("Strategy for each file:")
        dropdown_layout.addWidget(dropdown_label)

        self.strategy_combo = QComboBox()
        self.strategy_combo.addItem("Select All Fields (per file)")
        self.strategy_combo.addItem("Common Fields Only")
        self.strategy_combo.addItem("Smart Auto (recommended)")
        self.strategy_combo.setFixedWidth(300)
        dropdown_layout.addWidget(self.strategy_combo)
        dropdown_layout.addStretch()

        step3_layout.addLayout(dropdown_layout)
        step3_group.setLayout(step3_layout)
        layout.addWidget(step3_group)

        # Step 3: Convert
        step4_group = QGroupBox("Step 3: Convert to CSV")
        step4_layout = QHBoxLayout()

        self.convert_button = QPushButton("Convert All Files")
        self.convert_button.setStyleSheet(GREEN_BUTTON_STYLE)
        self.convert_button.clicked.connect(self.convert_files)
        self.convert_button.setEnabled(False)
        step4_layout.addWidget(self.convert_button)

        self.completion_label = QLabel("")
        self.completion_label.setStyleSheet("color: #4CAF50;")
        step4_layout.addWidget(self.completion_label)

        step4_layout.addStretch()

        step4_group.setLayout(step4_layout)
        layout.addWidget(step4_group)

        layout.addStretch()
        return tab

    def create_split_tab(self) -> QWidget:
        """Create the Split tab content"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)

        # File info display
        info_group = QGroupBox("File Information")
        info_layout = QHBoxLayout()

        self.split_file_label = QLabel("No file selected")
        self.split_file_label.setStyleSheet("color: #666666;")
        info_layout.addWidget(self.split_file_label, 1)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # Step 1: Configure Split
        step2_group = QGroupBox("Step 1: Configure Split")
        step2_layout = QVBoxLayout()

        self.split_button_group = QButtonGroup()

        # By number of files
        files_layout = QHBoxLayout()
        self.split_by_files_radio = QRadioButton("Split into")
        self.split_by_files_radio.setChecked(True)
        self.split_button_group.addButton(self.split_by_files_radio)
        files_layout.addWidget(self.split_by_files_radio)

        self.split_num_files_spin = QSpinBox()
        self.split_num_files_spin.setRange(2, 1000)
        self.split_num_files_spin.setValue(10)
        self.split_num_files_spin.setFixedWidth(80)
        files_layout.addWidget(self.split_num_files_spin)

        files_layout.addWidget(QLabel("files"))
        files_layout.addStretch()
        step2_layout.addLayout(files_layout)

        # By rows per file
        rows_layout = QHBoxLayout()
        self.split_by_rows_radio = QRadioButton("Split by")
        self.split_button_group.addButton(self.split_by_rows_radio)
        rows_layout.addWidget(self.split_by_rows_radio)

        self.split_rows_spin = QSpinBox()
        self.split_rows_spin.setRange(1, 10000000)
        self.split_rows_spin.setValue(1000)
        self.split_rows_spin.setFixedWidth(100)
        rows_layout.addWidget(self.split_rows_spin)

        rows_layout.addWidget(QLabel("rows per file"))
        rows_layout.addStretch()
        step2_layout.addLayout(rows_layout)

        # By file size
        size_layout = QHBoxLayout()
        self.split_by_size_radio = QRadioButton("Split by")
        self.split_button_group.addButton(self.split_by_size_radio)
        size_layout.addWidget(self.split_by_size_radio)

        self.split_size_spin = QSpinBox()
        self.split_size_spin.setRange(1, 1000000)
        self.split_size_spin.setValue(1000)
        self.split_size_spin.setFixedWidth(100)
        size_layout.addWidget(self.split_size_spin)

        size_layout.addWidget(QLabel("KB per file"))
        size_layout.addStretch()
        step2_layout.addLayout(size_layout)

        step2_group.setLayout(step2_layout)
        layout.addWidget(step2_group)

        # Step 2: Output Settings
        step3_group = QGroupBox("Step 2: Output Settings")
        step3_layout = QVBoxLayout()

        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Output Format:"))

        self.split_format_combo = QComboBox()
        self.split_format_combo.addItem("CSV", FileFormat.CSV)
        self.split_format_combo.addItem("JSON", FileFormat.JSON)
        self.split_format_combo.addItem("JSONL", FileFormat.JSONL)
        self.split_format_combo.setFixedWidth(150)
        format_layout.addWidget(self.split_format_combo)

        format_layout.addStretch()
        step3_layout.addLayout(format_layout)

        dir_layout = QHBoxLayout()
        dir_layout.addWidget(QLabel("Output Directory:"))

        self.split_output_dir_edit = QLineEdit()
        self.split_output_dir_edit.setPlaceholderText("Same as input file")
        dir_layout.addWidget(self.split_output_dir_edit, 1)

        self.split_output_dir_button = QPushButton("Browse...")
        self.split_output_dir_button.clicked.connect(self.split_browse_output_dir)
        dir_layout.addWidget(self.split_output_dir_button)

        step3_layout.addLayout(dir_layout)

        step3_group.setLayout(step3_layout)
        layout.addWidget(step3_group)

        # Step 3: Execute Split
        step4_group = QGroupBox("Step 3: Split File")
        step4_layout = QHBoxLayout()

        self.split_button = QPushButton("Split File")
        self.split_button.setStyleSheet(GREEN_BUTTON_STYLE)
        self.split_button.clicked.connect(self.execute_split)
        self.split_button.setEnabled(False)
        step4_layout.addWidget(self.split_button)

        self.split_status_label = QLabel("")
        self.split_status_label.setStyleSheet("color: #4CAF50;")
        step4_layout.addWidget(self.split_status_label)

        step4_layout.addStretch()

        step4_group.setLayout(step4_layout)
        layout.addWidget(step4_group)

        layout.addStretch()
        return tab

    def create_merge_tab(self) -> QWidget:
        """Create the Merge tab content"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)

        # File list info display
        info_group = QGroupBox("Selected Files")
        info_layout = QVBoxLayout()

        buttons_layout = QHBoxLayout()
        self.merge_remove_button = QPushButton("Remove Last")
        self.merge_remove_button.clicked.connect(self.merge_remove_files)
        buttons_layout.addWidget(self.merge_remove_button)

        self.merge_clear_button = QPushButton("Clear All")
        self.merge_clear_button.clicked.connect(self.merge_clear_files)
        buttons_layout.addWidget(self.merge_clear_button)

        buttons_layout.addStretch()
        info_layout.addLayout(buttons_layout)

        self.merge_file_list = QTextEdit()
        self.merge_file_list.setMaximumHeight(80)
        self.merge_file_list.setReadOnly(True)
        self.merge_file_list.setPlainText("No files selected")
        info_layout.addWidget(self.merge_file_list)

        self.merge_file_count_label = QLabel("0 files, 0 total records")
        info_layout.addWidget(self.merge_file_count_label)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # Step 1: Schema Handling
        step2_group = QGroupBox("Step 1: Schema Handling")
        step2_layout = QVBoxLayout()

        self.merge_schema_group = QButtonGroup()

        self.merge_union_radio = QRadioButton("Union of all fields (include all fields from all files)")
        self.merge_union_radio.setChecked(True)
        self.merge_schema_group.addButton(self.merge_union_radio)
        step2_layout.addWidget(self.merge_union_radio)

        self.merge_intersection_radio = QRadioButton("Common fields only (only fields present in ALL files)")
        self.merge_schema_group.addButton(self.merge_intersection_radio)
        step2_layout.addWidget(self.merge_intersection_radio)

        self.merge_first_radio = QRadioButton("First file's schema (use first file as template)")
        self.merge_schema_group.addButton(self.merge_first_radio)
        step2_layout.addWidget(self.merge_first_radio)

        self.merge_schema_info_label = QLabel("")
        self.merge_schema_info_label.setStyleSheet("color: #666666; margin-top: 5px;")
        step2_layout.addWidget(self.merge_schema_info_label)

        step2_group.setLayout(step2_layout)
        layout.addWidget(step2_group)

        # Step 2: Output Settings
        step3_group = QGroupBox("Step 2: Output Settings")
        step3_layout = QVBoxLayout()

        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Output Format:"))

        self.merge_format_combo = QComboBox()
        self.merge_format_combo.addItem("CSV", FileFormat.CSV)
        self.merge_format_combo.addItem("JSON", FileFormat.JSON)
        self.merge_format_combo.addItem("JSONL", FileFormat.JSONL)
        self.merge_format_combo.setFixedWidth(150)
        format_layout.addWidget(self.merge_format_combo)

        format_layout.addStretch()
        step3_layout.addLayout(format_layout)

        file_layout = QHBoxLayout()
        file_layout.addWidget(QLabel("Output File:"))

        self.merge_output_file_edit = QLineEdit()
        self.merge_output_file_edit.setPlaceholderText("merged.csv")
        file_layout.addWidget(self.merge_output_file_edit, 1)

        self.merge_output_file_button = QPushButton("Browse...")
        self.merge_output_file_button.clicked.connect(self.merge_browse_output_file)
        file_layout.addWidget(self.merge_output_file_button)

        step3_layout.addLayout(file_layout)

        step3_group.setLayout(step3_layout)
        layout.addWidget(step3_group)

        # Step 3: Execute Merge
        step4_group = QGroupBox("Step 3: Merge Files")
        step4_layout = QHBoxLayout()

        self.merge_button = QPushButton("Merge Files")
        self.merge_button.setStyleSheet(GREEN_BUTTON_STYLE)
        self.merge_button.clicked.connect(self.execute_merge)
        self.merge_button.setEnabled(False)
        step4_layout.addWidget(self.merge_button)

        self.merge_status_label = QLabel("")
        self.merge_status_label.setStyleSheet("color: #4CAF50;")
        step4_layout.addWidget(self.merge_status_label)

        step4_layout.addStretch()

        step4_group.setLayout(step4_layout)
        layout.addWidget(step4_group)

        layout.addStretch()
        return tab

    def setup_file_selection(self, parent_layout):
        """Shared file selection section at the top"""
        file_group = QGroupBox("Select File(s)")
        file_layout = QVBoxLayout()

        # Browse button and file display
        browse_layout = QHBoxLayout()

        self.main_browse_button = QPushButton("Browse for File(s)")
        self.main_browse_button.setStyleSheet(GREEN_BUTTON_STYLE)
        self.main_browse_button.clicked.connect(self.browse_main_files)
        browse_layout.addWidget(self.main_browse_button)

        self.main_file_display = QTextEdit()
        self.main_file_display.setMaximumHeight(60)
        self.main_file_display.setReadOnly(True)
        self.main_file_display.setPlainText("No files selected")
        browse_layout.addWidget(self.main_file_display, 1)

        self.main_file_count_label = QLabel("0 files selected")
        browse_layout.addWidget(self.main_file_count_label)

        file_layout.addLayout(browse_layout)
        file_group.setLayout(file_layout)
        parent_layout.addWidget(file_group)

    def setup_status_log(self, parent_layout):
        """Status Log"""
        log_group = QGroupBox("Status Log")
        log_layout = QVBoxLayout()

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Monaco", 9))
        log_layout.addWidget(self.log_text)

        log_group.setLayout(log_layout)
        parent_layout.addWidget(log_group, 1)

    def browse_main_files(self):
        """Browse for files from main file selection area"""
        # Determine which tab is active and what kind of selection to use
        current_tab_index = self.tab_widget.currentIndex()

        if current_tab_index == 0:  # Convert tab - multiple files
            files, _ = QFileDialog.getOpenFileNames(
                self,
                "Select files to convert",
                "",
                FILE_FILTER
            )
            if files:
                self.selected_files = files
                self.update_main_file_display()
                self.log_message(f"{len(self.selected_files)} files selected for conversion")
                self.analyze_schemas()

        elif current_tab_index == 1:  # Split tab - single file
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Select file to split",
                "",
                FILE_FILTER
            )
            if file_path:
                self.split_input_file = Path(file_path)
                self.update_main_file_display()
                try:
                    info = get_file_info(self.split_input_file)
                    self.split_file_label.setText(
                        f"{info['name']} ({info['format'].upper()}, {info['record_count']:,} records, {info['size_kb']:.1f} KB)"
                    )
                    self.split_file_label.setStyleSheet("color: #4CAF50;")
                    self.split_button.setEnabled(True)
                    self.log_message(f"Selected for split: {info['name']} ({info['record_count']:,} records)")
                except Exception as e:
                    self.split_file_label.setText(f"Error reading file: {e}")
                    self.split_file_label.setStyleSheet("color: #f44336;")
                    self.split_button.setEnabled(False)

        else:  # Merge tab - multiple files
            files, _ = QFileDialog.getOpenFileNames(
                self,
                "Select files to merge",
                "",
                FILE_FILTER
            )
            if files:
                for file_path in files:
                    path = Path(file_path)
                    if path not in self.merge_input_files:
                        self.merge_input_files.append(path)
                self.update_main_file_display()
                self.update_merge_file_list()

    def update_main_file_display(self):
        """Update the main file display based on current tab"""
        current_tab_index = self.tab_widget.currentIndex()

        if current_tab_index == 0:  # Convert tab
            if self.selected_files:
                file_names = [Path(f).name for f in self.selected_files]
                self.main_file_display.setPlainText("\n".join(file_names))
                self.main_file_count_label.setText(f"{len(self.selected_files)} files selected")
            else:
                self.main_file_display.setPlainText("No files selected")
                self.main_file_count_label.setText("0 files selected")

        elif current_tab_index == 1:  # Split tab
            if self.split_input_file:
                self.main_file_display.setPlainText(self.split_input_file.name)
                self.main_file_count_label.setText("1 file selected")
            else:
                self.main_file_display.setPlainText("No file selected")
                self.main_file_count_label.setText("0 files selected")

        else:  # Merge tab
            if self.merge_input_files:
                file_names = [f.name for f in self.merge_input_files]
                self.main_file_display.setPlainText("\n".join(file_names))
                self.main_file_count_label.setText(f"{len(self.merge_input_files)} files selected")
            else:
                self.main_file_display.setPlainText("No files selected")
                self.main_file_count_label.setText("0 files selected")

    def on_tab_changed(self, index):
        """Handle tab changes to update file display"""
        self.update_main_file_display()

        # Update button text based on tab
        if index == 0:  # Convert
            self.main_browse_button.setText("Browse for File(s)")
        elif index == 1:  # Split
            self.main_browse_button.setText("Browse for File")
        else:  # Merge
            self.main_browse_button.setText("Add File(s) to Merge")

    def log_message(self, message):
        """Add timestamped message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"{timestamp} - {message}"
        self.log_text.append(log_entry)
        QApplication.processEvents()

    # ==================== Convert Tab Methods ====================

    def analyze_schemas(self):
        """Start schema analysis in background thread"""
        self.log_message("Analyzing file schemas...")

        self.analyzer_thread = SchemaAnalyzerThread(self.selected_files)
        self.analyzer_thread.progress.connect(self.log_message)
        self.analyzer_thread.finished.connect(self.update_analysis_results)
        self.analyzer_thread.start()

    def update_analysis_results(self, file_schemas, field_frequency, all_fields, schemas, total_records):
        """Update UI with analysis results"""
        self.file_schemas = file_schemas
        self.field_frequency = field_frequency
        self.all_fields = all_fields

        num_files = len(self.selected_files)
        num_fields = len(all_fields)

        schemas_list = list(file_schemas.values())
        all_schemas_identical = all(schema == schemas_list[0] for schema in schemas_list) if schemas_list else True

        if all_schemas_identical:
            self.analysis_label.setText(
                f"All files have the same schema ({num_fields} fields across {num_files} files, {total_records:,} total records)"
            )
            self.analysis_label.setStyleSheet("color: #4CAF50;")
        else:
            self.analysis_label.setText(
                f"Files have varying schemas ({num_fields} unique fields across {num_files} files, {total_records:,} total records)"
            )
            self.analysis_label.setStyleSheet("color: #ff9800;")

        # Update strategy button labels
        smart_auto_count = len([f for f, c in field_frequency.items() if c >= max(1, int(0.7 * num_files))])
        common_count = len([f for f, c in field_frequency.items() if c == num_files])

        if file_schemas:
            richest_file = max(file_schemas.keys(), key=lambda f: len(file_schemas[f]))
            richest_count = len(file_schemas[richest_file])
            richest_name = Path(richest_file).name
        else:
            richest_count = 0
            richest_name = "file.json"

        strategy_texts = [
            ("smart_auto", f"Merge with Smart Auto - Fields in 70%+ of files ({smart_auto_count} fields)"),
            ("all_available", f"Merge with All Available - Union of all fields ({num_fields} fields)"),
            ("common_only", f"Merge with Common Only - Fields in ALL files ({common_count} fields)"),
            ("most_complete", f"Merge with Most Complete File - Use '{richest_name}' ({richest_count} fields)"),
            ("separate", "Keep Files Separate - Individual CSVs with own fields")
        ]

        for (value, button), (_, text) in zip(self.strategy_buttons, strategy_texts):
            button.setText(text)

        self.step3_group.setEnabled(True)
        self.convert_button.setEnabled(True)

        self.log_message(f"Schema analysis complete: {num_fields} unique fields found")

    def strategy_changed(self, strategy):
        """Handle strategy selection change"""
        self.selected_strategy = strategy
        strategy_names = {
            "smart_auto": "Smart Auto",
            "all_available": "All Available",
            "common_only": "Common Only",
            "most_complete": "Most Complete File",
            "separate": "Keep Files Separate"
        }
        self.log_message(f"Strategy selected: {strategy_names.get(strategy, strategy)}")

    def convert_files(self):
        """Start file conversion"""
        if not self.selected_files:
            return

        output_dir = QFileDialog.getExistingDirectory(
            self,
            "Select output directory for CSV files"
        )

        if not output_dir:
            return

        self.convert_button.setEnabled(False)
        self.log_message("Starting conversion...")

        self.conversion_thread = ConversionThread(
            self.selected_files,
            self.selected_strategy,
            None,
            output_dir,
            self.file_schemas,
            self.all_fields
        )
        self.conversion_thread.progress.connect(self.log_message)
        self.conversion_thread.file_complete.connect(
            lambda f, r: self.log_message(f"{f}: {r:,} records converted")
        )
        self.conversion_thread.finished.connect(self.conversion_complete)
        self.conversion_thread.start()

    def conversion_complete(self, num_files, total_records):
        """Handle conversion completion"""
        self.completion_label.setText("Batch conversion complete!")
        self.convert_button.setEnabled(True)
        self.log_message(f"Batch conversion complete: {num_files} files, {total_records:,} total records")

        QMessageBox.information(
            self,
            "Conversion Complete",
            f"Successfully converted {num_files} files with {total_records:,} total records"
        )

    # ==================== Split Tab Methods ====================

    def split_browse_output_dir(self):
        """Browse for split output directory"""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Select output directory for split files"
        )
        if dir_path:
            self.split_output_dir_edit.setText(dir_path)

    def execute_split(self):
        """Execute the file split operation"""
        if not self.split_input_file:
            return

        # Determine split mode
        if self.split_by_files_radio.isChecked():
            split_mode = "by_files"
            num_files = self.split_num_files_spin.value()
            rows_per_file = None
            size_kb = None
        elif self.split_by_rows_radio.isChecked():
            split_mode = "by_rows"
            num_files = None
            rows_per_file = self.split_rows_spin.value()
            size_kb = None
        else:
            split_mode = "by_size"
            num_files = None
            rows_per_file = None
            size_kb = self.split_size_spin.value()

        # Get output format
        output_format = self.split_format_combo.currentData()

        # Get output directory
        output_dir_text = self.split_output_dir_edit.text().strip()
        if output_dir_text:
            output_dir = Path(output_dir_text)
        else:
            output_dir = self.split_input_file.parent

        # Create split options
        split_options = SplitOptions(
            split_mode=split_mode,
            num_files=num_files,
            rows_per_file=rows_per_file,
            size_kb=size_kb,
            output_format=output_format,
            output_dir=output_dir
        )

        self.split_button.setEnabled(False)
        self.split_status_label.setText("")
        self.log_message(f"Starting split ({split_mode})...")

        # Start split thread
        self.split_thread = SplitThread(self.split_input_file, split_options)
        self.split_thread.progress.connect(self.log_message)
        self.split_thread.file_created.connect(
            lambda f, r: self.log_message(f"Created: {f} ({r:,} records)")
        )
        self.split_thread.finished.connect(self.split_complete)
        self.split_thread.error.connect(self.split_error)
        self.split_thread.start()

    def split_complete(self, num_files, total_records):
        """Handle split completion"""
        self.split_button.setEnabled(True)
        self.split_status_label.setText(f"Created {num_files} files")
        self.log_message(f"Split complete: {num_files} files, {total_records:,} total records")

        QMessageBox.information(
            self,
            "Split Complete",
            f"Successfully split into {num_files} files with {total_records:,} total records"
        )

    def split_error(self, error_message):
        """Handle split error"""
        self.split_button.setEnabled(True)
        self.split_status_label.setText("Error!")
        self.split_status_label.setStyleSheet("color: #f44336;")
        self.log_message(f"Split error: {error_message}")

        QMessageBox.critical(
            self,
            "Split Error",
            f"Error splitting file: {error_message}"
        )

    # ==================== Merge Tab Methods ====================

    def merge_remove_files(self):
        """Remove selected files from merge list"""
        # For simplicity, just clear the last file
        if self.merge_input_files:
            removed = self.merge_input_files.pop()
            self.log_message(f"Removed: {removed.name}")
            self.update_main_file_display()
            self.update_merge_file_list()

    def merge_clear_files(self):
        """Clear all files from merge list"""
        self.merge_input_files = []
        self.update_main_file_display()
        self.update_merge_file_list()

    def update_merge_file_list(self):
        """Update the merge file list display"""
        if not self.merge_input_files:
            self.merge_file_list.setPlainText("No files selected")
            self.merge_file_count_label.setText("0 files, 0 total records")
            self.merge_button.setEnabled(False)
            self.merge_schema_info_label.setText("")
            return

        # Build file list with info
        lines = []
        total_records = 0

        for file_path in self.merge_input_files:
            try:
                info = get_file_info(file_path)
                lines.append(f"{info['name']} ({info['format'].upper()}, {info['record_count']:,} records)")
                total_records += info['record_count']
            except Exception:
                lines.append(f"{file_path.name} (error reading)")

        self.merge_file_list.setPlainText("\n".join(lines))
        self.merge_file_count_label.setText(f"{len(self.merge_input_files)} files, {total_records:,} total records")
        self.merge_button.setEnabled(len(self.merge_input_files) >= 2)

        # Update schema info
        if len(self.merge_input_files) >= 2:
            try:
                merger = FileMerger(MergeOptions())
                preview = merger.get_schema_preview(self.merge_input_files)
                self.merge_schema_info_label.setText(
                    f"Preview: {preview['field_count']} fields, {preview['total_records']:,} records"
                )
            except Exception:
                self.merge_schema_info_label.setText("")

        self.log_message(f"Merge list updated: {len(self.merge_input_files)} files")

    def merge_browse_output_file(self):
        """Browse for merge output file"""
        # Get extension based on format
        output_format = self.merge_format_combo.currentData()
        ext_map = {
            FileFormat.CSV: "CSV Files (*.csv)",
            FileFormat.JSON: "JSON Files (*.json)",
            FileFormat.JSONL: "JSONL Files (*.jsonl)",
        }
        filter_str = ext_map.get(output_format, "All Files (*.*)")

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Select output file for merge",
            "",
            filter_str
        )
        if file_path:
            self.merge_output_file_edit.setText(file_path)

    def execute_merge(self):
        """Execute the file merge operation"""
        if len(self.merge_input_files) < 2:
            return

        # Get schema strategy
        if self.merge_union_radio.isChecked():
            schema_strategy = "union"
        elif self.merge_intersection_radio.isChecked():
            schema_strategy = "intersection"
        else:
            schema_strategy = "first_file"

        # Get output format
        output_format = self.merge_format_combo.currentData()

        # Get output path
        output_path_text = self.merge_output_file_edit.text().strip()
        if output_path_text:
            output_path = Path(output_path_text)
        else:
            ext_map = {
                FileFormat.CSV: '.csv',
                FileFormat.JSON: '.json',
                FileFormat.JSONL: '.jsonl',
            }
            ext = ext_map.get(output_format, '.csv')
            output_path = self.merge_input_files[0].parent / f"merged{ext}"

        # Create merge options
        merge_options = MergeOptions(
            output_format=output_format,
            output_path=output_path,
            schema_strategy=schema_strategy
        )

        self.merge_button.setEnabled(False)
        self.merge_status_label.setText("")
        self.log_message(f"Starting merge ({schema_strategy} schema)...")

        # Start merge thread
        self.merge_thread = MergeThread(self.merge_input_files, merge_options)
        self.merge_thread.progress.connect(self.log_message)
        self.merge_thread.finished.connect(self.merge_complete)
        self.merge_thread.error.connect(self.merge_error)
        self.merge_thread.start()

    def merge_complete(self, output_path, total_records):
        """Handle merge completion"""
        self.merge_button.setEnabled(True)
        self.merge_status_label.setText(f"Created: {Path(output_path).name}")
        self.log_message(f"Merge complete: {output_path} ({total_records:,} records)")

        QMessageBox.information(
            self,
            "Merge Complete",
            f"Successfully merged {len(self.merge_input_files)} files into {Path(output_path).name}\n"
            f"Total records: {total_records:,}"
        )

    def merge_error(self, error_message):
        """Handle merge error"""
        self.merge_button.setEnabled(True)
        self.merge_status_label.setText("Error!")
        self.merge_status_label.setStyleSheet("color: #f44336;")
        self.log_message(f"Merge error: {error_message}")

        QMessageBox.critical(
            self,
            "Merge Error",
            f"Error merging files: {error_message}"
        )


def main():
    app = QApplication(sys.argv)
    converter = MultiFileConverter()
    converter.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
