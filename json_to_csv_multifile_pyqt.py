#!/usr/bin/env python3
"""
JSON to CSV Converter (Multi-File) - PyQt6 Version
Recreates the exact interface shown in the screenshot
"""

import sys
import json
import csv
import os
from pathlib import Path
from collections import Counter
from datetime import datetime

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QGroupBox, QPushButton, QTextEdit, 
                            QLabel, QRadioButton, QComboBox, QFileDialog,
                            QMessageBox, QButtonGroup)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor


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
            except Exception as e:
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


class MultiFileConverter(QMainWindow):
    def __init__(self):
        super().__init__()
        self.selected_files = []
        self.file_schemas = {}
        self.all_fields = set()
        self.field_frequency = {}
        self.selected_strategy = "separate"
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI"""
        self.setWindowTitle("JSON to CSV Converter (Multi-File)")
        self.setGeometry(100, 100, 1200, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title_label = QLabel("JSON to CSV Converter (Multi-File)")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)
        
        # Step 1: Select JSON Files
        self.setup_step1(main_layout)
        
        # Step 2: Schema Analysis
        self.setup_step2(main_layout)
        
        # Step 3: Field Selection
        self.setup_step3(main_layout)
        
        # Step 4: Convert to CSV
        self.setup_step4(main_layout)
        
        # Status Log
        self.setup_status_log(main_layout)
    
    def setup_step1(self, parent_layout):
        """Step 1: Select JSON Files"""
        step1_group = QGroupBox("Step 1: Select JSON Files")
        step1_layout = QHBoxLayout()
        
        # Browse button (green)
        self.browse_button = QPushButton("Browse for JSON Files")
        self.browse_button.setStyleSheet("""
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
        """)
        self.browse_button.clicked.connect(self.browse_files)
        step1_layout.addWidget(self.browse_button)
        
        # File list display
        self.file_list_text = QTextEdit()
        self.file_list_text.setMaximumHeight(80)
        self.file_list_text.setReadOnly(True)
        self.file_list_text.setPlainText("No files selected")
        step1_layout.addWidget(self.file_list_text, 1)
        
        # File count
        self.file_count_label = QLabel("0 files selected")
        step1_layout.addWidget(self.file_count_label)
        
        step1_group.setLayout(step1_layout)
        parent_layout.addWidget(step1_group)
    
    def setup_step2(self, parent_layout):
        """Step 2: Schema Analysis"""
        step2_group = QGroupBox("Step 2: Schema Analysis")
        step2_layout = QVBoxLayout()
        
        # Analysis label
        self.analysis_label = QLabel("Select files to analyze schemas")
        self.analysis_label.setStyleSheet("color: #666666;")
        step2_layout.addWidget(self.analysis_label)
        
        step2_group.setLayout(step2_layout)
        parent_layout.addWidget(step2_group)
    
    def setup_step3(self, parent_layout):
        """Step 3: Field Selection"""
        step3_group = QGroupBox("Step 3: Field Selection")
        step3_layout = QVBoxLayout()
        
        # Store reference to step3 group to enable/disable it
        self.step3_group = step3_group
        self.step3_group.setEnabled(False)  # Disabled until files are analyzed
        
        # Strategy description
        desc_label = QLabel("Files have different schemas. Choose field selection strategy:")
        step3_layout.addWidget(desc_label)
        
        # Radio buttons
        self.button_group = QButtonGroup()
        self.strategy_buttons = []
        
        strategies = [
            ("smart_auto", "🔘 Merge with Smart Auto - Fields in 70%+ of files (0 fields)"),
            ("all_available", "🔘 Merge with All Available - Union of all fields (0 fields)"),
            ("common_only", "🔘 Merge with Common Only - Fields in ALL files (0 fields)"),
            ("most_complete", "🔘 Merge with Most Complete File - Use 'file.json' (0 fields)"),
            ("separate", "☑️ Keep Files Separate - Individual CSVs with own fields")
        ]
        
        for i, (value, text) in enumerate(strategies):
            radio = QRadioButton(text)
            # Remove grey styling - use default checkbox appearance
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
        self.strategy_combo.addItem("✓ Select All Fields (per file)")
        self.strategy_combo.addItem("Common Fields Only")
        self.strategy_combo.addItem("Smart Auto (recommended)")
        dropdown_layout.addWidget(self.strategy_combo)
        dropdown_layout.addStretch()
        
        step3_layout.addLayout(dropdown_layout)
        
        step3_group.setLayout(step3_layout)
        parent_layout.addWidget(step3_group)
    
    def setup_step4(self, parent_layout):
        """Step 4: Convert to CSV"""
        step4_group = QGroupBox("Step 4: Convert to CSV")
        step4_layout = QHBoxLayout()
        
        # Convert button (green)
        self.convert_button = QPushButton("🚀 Convert All Files")
        self.convert_button.setStyleSheet("""
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
        """)
        self.convert_button.clicked.connect(self.convert_files)
        self.convert_button.setEnabled(False)
        step4_layout.addWidget(self.convert_button)
        
        # Completion label
        self.completion_label = QLabel("")
        self.completion_label.setStyleSheet("color: #4CAF50;")
        step4_layout.addWidget(self.completion_label)
        
        step4_layout.addStretch()
        
        step4_group.setLayout(step4_layout)
        parent_layout.addWidget(step4_group)
    
    def setup_status_log(self, parent_layout):
        """Status Log"""
        log_group = QGroupBox("Status Log")
        log_layout = QVBoxLayout()
        
        # Log text area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Monaco", 9))
        log_layout.addWidget(self.log_text)
        
        log_group.setLayout(log_layout)
        parent_layout.addWidget(log_group, 1)  # Give it more space
    
    def log_message(self, message):
        """Add timestamped message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"{timestamp} - {message}"
        self.log_text.append(log_entry)
        # Force update
        QApplication.processEvents()
    
    def browse_files(self):
        """Browse for JSON files"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select JSON files to convert",
            "",
            "JSON Files (*.json);;All Files (*.*)"
        )
        
        if files:
            self.selected_files = files
            self.update_file_display()
            self.log_message(f"{len(self.selected_files)} files selected")
            self.analyze_schemas()
    
    def update_file_display(self):
        """Update the file list display"""
        file_names = [Path(f).name for f in self.selected_files]
        self.file_list_text.setPlainText("\n".join(file_names))
        self.file_count_label.setText(f"{len(self.selected_files)} files selected")
    
    def analyze_schemas(self):
        """Start schema analysis in background thread"""
        self.log_message("Analyzing file schemas...")
        
        # Create and start analyzer thread
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
        
        # Check if all files have the same schema
        schemas_list = list(file_schemas.values())
        all_schemas_identical = all(schema == schemas_list[0] for schema in schemas_list) if schemas_list else True
        
        if all_schemas_identical:
            self.analysis_label.setText(
                f"✅ All files have the same schema ({num_fields} fields across {num_files} files, {total_records:,} total records)"
            )
            self.analysis_label.setStyleSheet("color: #4CAF50;")  # Green for same schema
        else:
            self.analysis_label.setText(
                f"⚠️ Files have varying schemas ({num_fields} unique fields across {num_files} files, {total_records:,} total records)"
            )
            self.analysis_label.setStyleSheet("color: #ff9800;")  # Orange for varying schemas
        
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
            ("smart_auto", f"🔘 Merge with Smart Auto - Fields in 70%+ of files ({smart_auto_count} fields)"),
            ("all_available", f"🔘 Merge with All Available - Union of all fields ({num_fields} fields)"),
            ("common_only", f"🔘 Merge with Common Only - Fields in ALL files ({common_count} fields)"),
            ("most_complete", f"🔘 Merge with Most Complete File - Use '{richest_name}' ({richest_count} fields)"),
            ("separate", "☑️ Keep Files Separate - Individual CSVs with own fields")
        ]
        
        for (value, button), (_, text) in zip(self.strategy_buttons, strategy_texts):
            button.setText(text)
        
        # Update radio button texts to show correct checked/unchecked state
        self.update_radio_button_texts()
        
        # Enable step 3 and convert button
        self.step3_group.setEnabled(True)
        self.convert_button.setEnabled(True)
        
        self.log_message(f"Schema analysis complete: {num_fields} unique fields found")
    
    def update_radio_button_texts(self):
        """Update radio button texts to show checked/unchecked state"""
        for value, button in self.strategy_buttons:
            current_text = button.text()
            # Remove existing emoji
            if current_text.startswith("🔘 ") or current_text.startswith("☑️ "):
                current_text = current_text[2:]
            
            # Add appropriate emoji based on checked state
            if button.isChecked():
                button.setText("☑️ " + current_text)
            else:
                button.setText("🔘 " + current_text)
    
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
        self.update_radio_button_texts()
    
    def convert_files(self):
        """Start file conversion"""
        if not self.selected_files:
            return
        
        # Choose output directory
        output_dir = QFileDialog.getExistingDirectory(
            self,
            "Select output directory for CSV files"
        )
        
        if not output_dir:
            return
        
        self.convert_button.setEnabled(False)
        self.log_message("Starting conversion...")
        
        # Create and start conversion thread
        self.conversion_thread = ConversionThread(
            self.selected_files,
            self.selected_strategy,
            None,  # selected_fields - simplified for now
            output_dir,
            self.file_schemas,
            self.all_fields
        )
        self.conversion_thread.progress.connect(self.log_message)
        self.conversion_thread.file_complete.connect(
            lambda f, r: self.log_message(f"✅ {f}: {r:,} records converted")
        )
        self.conversion_thread.finished.connect(self.conversion_complete)
        self.conversion_thread.start()
    
    def conversion_complete(self, num_files, total_records):
        """Handle conversion completion"""
        self.completion_label.setText("✅ Batch conversion complete!")
        self.convert_button.setEnabled(True)
        self.log_message(f"Batch conversion complete: {num_files} files, {total_records:,} total records")
        
        QMessageBox.information(
            self,
            "Conversion Complete",
            f"Successfully converted {num_files} files with {total_records:,} total records"
        )


def main():
    app = QApplication(sys.argv)
    converter = MultiFileConverter()
    converter.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()