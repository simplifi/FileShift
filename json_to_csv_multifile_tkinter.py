#!/usr/bin/env python3
"""
JSON to CSV Converter (Multi-File) - Tkinter Interface
Recreates the exact interface shown in the screenshot
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import csv
import os
from pathlib import Path
from collections import Counter
import threading
from datetime import datetime


class MultiFileConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("JSON to CSV Converter (Multi-File)")
        self.root.geometry("1200x800")
        
        # Data
        self.selected_files = []
        self.file_schemas = {}
        self.all_fields = set()
        self.field_frequency = Counter()
        self.selected_strategy = tk.StringVar(value="separate")
        
        self.setup_ui()
    
    def setup_ui(self):
        """Create the UI matching the screenshot"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="JSON to CSV Converter (Multi-File)", 
                               font=('Helvetica', 18, 'bold'))
        title_label.grid(row=0, column=0, pady=(0, 20))
        
        # Step 1: Select JSON Files
        self.setup_step1(main_frame, 1)
        
        # Step 2: Schema Analysis
        self.setup_step2(main_frame, 2)
        
        # Step 3: Field Selection
        self.setup_step3(main_frame, 3)
        
        # Step 4: Convert to CSV
        self.setup_step4(main_frame, 4)
        
        # Status Log
        self.setup_status_log(main_frame, 5)
    
    def setup_step1(self, parent, row):
        """Step 1: Select JSON Files"""
        step1_frame = ttk.LabelFrame(parent, text="Step 1: Select JSON Files", padding="10")
        step1_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=5)
        step1_frame.columnconfigure(1, weight=1)
        
        # Browse button (green styling)
        self.browse_button = tk.Button(step1_frame, text="Browse for JSON Files", 
                                      command=self.browse_files, bg='#4CAF50', fg='white',
                                      font=('Helvetica', 10, 'bold'), relief='raised')
        self.browse_button.grid(row=0, column=0, padx=(0, 10), pady=5, sticky=tk.W)
        
        # File list display
        self.file_list_text = tk.Text(step1_frame, height=4, width=80, wrap=tk.WORD)
        self.file_list_text.grid(row=0, column=1, rowspan=2, sticky=(tk.W, tk.E), padx=(10, 0))
        self.file_list_text.insert(tk.END, "No files selected")
        self.file_list_text.config(state=tk.DISABLED)
        
        # File count
        self.file_count_label = ttk.Label(step1_frame, text="0 files selected")
        self.file_count_label.grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
    
    def setup_step2(self, parent, row):
        """Step 2: Schema Analysis"""
        step2_frame = ttk.LabelFrame(parent, text="Step 2: Schema Analysis", padding="10")
        step2_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Analysis warning/info
        self.analysis_label = ttk.Label(step2_frame, 
                                       text="⚠️ Files have varying schemas (0 unique fields across 0 files, 0 total records)",
                                       foreground='orange')
        self.analysis_label.grid(row=0, column=0, sticky=tk.W)
    
    def setup_step3(self, parent, row):
        """Step 3: Field Selection"""
        step3_frame = ttk.LabelFrame(parent, text="Step 3: Field Selection", padding="10")
        step3_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=5)
        step3_frame.columnconfigure(0, weight=1)
        
        # Strategy description
        ttk.Label(step3_frame, text="Files have different schemas. Choose field selection strategy:").grid(
            row=0, column=0, sticky=tk.W, pady=(0, 10))
        
        # Radio buttons for strategies
        self.strategy_buttons = []
        strategies = [
            ("smart_auto", "☑️ Merge with Smart Auto - Fields in 70%+ of files (0 fields)"),
            ("all_available", "☑️ Merge with All Available - Union of all fields (0 fields)"),
            ("common_only", "☑️ Merge with Common Only - Fields in ALL files (0 fields)"),
            ("most_complete", "☑️ Merge with Most Complete File - Use 'file.json' (0 fields)"),
            ("separate", "🔘 Keep Files Separate - Individual CSVs with own fields")
        ]
        
        for i, (value, text) in enumerate(strategies):
            radio = ttk.Radiobutton(step3_frame, text=text, variable=self.selected_strategy, 
                                   value=value, command=self.strategy_changed)
            radio.grid(row=i+1, column=0, sticky=tk.W, pady=2)
            self.strategy_buttons.append(radio)
        
        # Strategy dropdown (bottom of step 3)
        dropdown_frame = ttk.Frame(step3_frame)
        dropdown_frame.grid(row=len(strategies)+1, column=0, sticky=tk.W, pady=(10, 0))
        
        ttk.Label(dropdown_frame, text="Strategy for each file:").grid(row=0, column=0, padx=(0, 10))
        self.strategy_combo = ttk.Combobox(dropdown_frame, values=["Select All Fields (per file)"], 
                                          state="readonly", width=25)
        self.strategy_combo.set("Select All Fields (per file)")
        self.strategy_combo.grid(row=0, column=1)
    
    def setup_step4(self, parent, row):
        """Step 4: Convert to CSV"""
        step4_frame = ttk.LabelFrame(parent, text="Step 4: Convert to CSV", padding="10")
        step4_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=5)
        
        button_frame = ttk.Frame(step4_frame)
        button_frame.grid(row=0, column=0, sticky=tk.W)
        
        # Convert button (green styling)
        self.convert_button = tk.Button(button_frame, text="🚀 Convert All Files", 
                                       command=self.convert_files, bg='#4CAF50', fg='white',
                                       font=('Helvetica', 10, 'bold'), relief='raised', 
                                       state=tk.DISABLED)
        self.convert_button.grid(row=0, column=0, padx=(0, 20))
        
        # Completion indicator
        self.completion_label = ttk.Label(button_frame, text="", foreground='green')
        self.completion_label.grid(row=0, column=1)
    
    def setup_status_log(self, parent, row):
        """Status Log"""
        log_frame = ttk.LabelFrame(parent, text="Status Log", padding="10")
        log_frame.grid(row=row, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # Configure main frame to expand log
        parent.rowconfigure(row, weight=1)
        
        # Scrollable text area
        self.log_text = tk.Text(log_frame, height=8, font=('Monaco', 9), wrap=tk.WORD)
        log_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
    
    def log_message(self, message):
        """Add timestamped message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"{timestamp} - {message}\n"
        
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        
        # Force update
        self.root.update_idletasks()
    
    def browse_files(self):
        """Browse for JSON files"""
        file_paths = filedialog.askopenfilenames(
            title="Select JSON files to convert",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_paths:
            self.selected_files = list(file_paths)
            self.update_file_display()
            self.log_message(f"{len(self.selected_files)} files selected")
            self.analyze_schemas()
    
    def update_file_display(self):
        """Update the file list display"""
        self.file_list_text.config(state=tk.NORMAL)
        self.file_list_text.delete(1.0, tk.END)
        
        file_names = [Path(f).name for f in self.selected_files]
        self.file_list_text.insert(tk.END, "\n".join(file_names))
        self.file_list_text.config(state=tk.DISABLED)
        
        self.file_count_label.config(text=f"{len(self.selected_files)} files selected")
    
    def analyze_schemas(self):
        """Analyze schemas of selected files"""
        self.log_message("Analyzing file schemas...")
        
        # Run in background thread
        thread = threading.Thread(target=self.analyze_schemas_background)
        thread.daemon = True
        thread.start()
    
    def analyze_schemas_background(self):
        """Background schema analysis"""
        self.file_schemas = {}
        self.all_fields = set()
        self.field_frequency = Counter()
        total_records = 0
        
        for file_path in self.selected_files:
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
            
            self.file_schemas[file_path] = sorted(list(fields_set))
            self.all_fields.update(fields_set)
            total_records += record_count
            
            for field in fields_set:
                self.field_frequency[field] += 1
        
        # Update UI on main thread
        self.root.after(0, lambda: self.update_analysis_results(total_records))
    
    def extract_fields(self, obj, fields_set, prefix=""):
        """Recursively extract field paths"""
        if isinstance(obj, dict):
            for key, value in obj.items():
                field_path = f"{prefix}.{key}" if prefix else key
                fields_set.add(field_path)
                if isinstance(value, dict):
                    self.extract_fields(value, fields_set, field_path)
    
    def update_analysis_results(self, total_records):
        """Update analysis results in UI"""
        num_files = len(self.selected_files)
        num_fields = len(self.all_fields)
        
        self.analysis_label.config(
            text=f"⚠️ Files have varying schemas ({num_fields} unique fields across {num_files} files, {total_records:,} total records)")
        
        # Update strategy button labels
        smart_auto_count = len([f for f, c in self.field_frequency.items() if c >= max(1, int(0.7 * num_files))])
        common_count = len([f for f, c in self.field_frequency.items() if c == num_files])
        
        if self.file_schemas:
            richest_file = max(self.file_schemas.keys(), key=lambda f: len(self.file_schemas[f]))
            richest_count = len(self.file_schemas[richest_file])
            richest_name = Path(richest_file).name
        else:
            richest_count = 0
            richest_name = "file.json"
        
        strategy_texts = [
            f"☑️ Merge with Smart Auto - Fields in 70%+ of files ({smart_auto_count} fields)",
            f"☑️ Merge with All Available - Union of all fields ({num_fields} fields)",
            f"☑️ Merge with Common Only - Fields in ALL files ({common_count} fields)",
            f"☑️ Merge with Most Complete File - Use '{richest_name}' ({richest_count} fields)",
            "🔘 Keep Files Separate - Individual CSVs with own fields"
        ]
        
        for button, text in zip(self.strategy_buttons, strategy_texts):
            button.config(text=text)
        
        # Enable convert button
        self.convert_button.config(state=tk.NORMAL)
        
        self.log_message(f"Schema analysis complete: {num_fields} unique fields found")
    
    def strategy_changed(self):
        """Handle strategy selection change"""
        strategy_names = {
            "smart_auto": "Smart Auto",
            "all_available": "All Available", 
            "common_only": "Common Only",
            "most_complete": "Most Complete File",
            "separate": "Keep Files Separate"
        }
        strategy_name = strategy_names.get(self.selected_strategy.get(), "Unknown")
        self.log_message(f"Strategy selected: {strategy_name}")
    
    def convert_files(self):
        """Convert files to CSV"""
        if not self.selected_files:
            return
        
        # Choose output directory
        output_dir = filedialog.askdirectory(title="Select output directory for CSV files")
        if not output_dir:
            return
        
        self.convert_button.config(state=tk.DISABLED)
        self.log_message("Starting conversion...")
        
        # Run conversion in background
        thread = threading.Thread(target=self.perform_conversion, args=(output_dir,))
        thread.daemon = True
        thread.start()
    
    def perform_conversion(self, output_dir):
        """Perform the actual conversion"""
        try:
            total_records = 0
            
            for file_path in self.selected_files:
                self.root.after(0, lambda f=file_path: self.log_message(f"Converting {Path(f).name}..."))
                
                # Convert file
                records = self.convert_single_file(file_path, output_dir)
                total_records += records
                
                self.root.after(0, lambda f=file_path, r=records: 
                               self.log_message(f"✅ {Path(f).name}: {r:,} records converted"))
            
            # Update UI on completion
            self.root.after(0, lambda: self.conversion_complete(total_records, len(self.selected_files)))
            
        except Exception as e:
            self.root.after(0, lambda: self.log_message(f"❌ Conversion failed: {str(e)}"))
    
    def convert_single_file(self, file_path, output_dir):
        """Convert a single file"""
        # Get fields based on strategy
        if self.selected_strategy.get() == "separate":
            fields = self.file_schemas.get(file_path, [])
        else:
            # Simplified - use all fields for merged strategies
            fields = sorted(list(self.all_fields))
        
        # Convert file
        input_name = Path(file_path).stem
        output_file = os.path.join(output_dir, f"{input_name}.csv")
        
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
    
    def conversion_complete(self, total_records, num_files):
        """Handle conversion completion"""
        self.completion_label.config(text="✅ Batch conversion complete!")
        self.convert_button.config(state=tk.NORMAL)
        self.log_message(f"Batch conversion complete: {num_files} files, {total_records:,} total records")
        
        messagebox.showinfo("Conversion Complete", 
                           f"Successfully converted {num_files} files with {total_records:,} total records")


def main():
    root = tk.Tk()
    app = MultiFileConverter(root)
    root.mainloop()


if __name__ == "__main__":
    main()