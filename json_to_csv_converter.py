#!/usr/bin/env python3
"""
JSON to CSV Converter - GUI Application
Handles large NDJSON (newline-delimited JSON) files efficiently
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import json
import csv
import os
import threading
from collections import OrderedDict
from datetime import datetime


class JSONtoCSVConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("JSON to CSV Converter")
        self.root.geometry("800x600")
        
        # Variables
        self.input_file = tk.StringVar()
        self.output_file = tk.StringVar()
        self.selected_fields = []
        self.all_fields = []
        self.preview_data = []
        self.total_records = 0
        
        # Create GUI
        self.create_widgets()
        
    def create_widgets(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Input file section
        ttk.Label(main_frame, text="Input JSON File:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.input_file, width=50).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(main_frame, text="Browse", command=self.browse_input).grid(row=0, column=2, padx=5)
        ttk.Button(main_frame, text="Analyze", command=self.analyze_file).grid(row=0, column=3)
        
        # File info
        self.info_label = ttk.Label(main_frame, text="No file loaded")
        self.info_label.grid(row=1, column=0, columnspan=4, sticky=tk.W, pady=5)
        
        # Field selection section
        ttk.Label(main_frame, text="Select Fields to Export:").grid(row=2, column=0, sticky=tk.W, pady=(20, 5))
        
        # Create frame for field selection
        field_frame = ttk.Frame(main_frame)
        field_frame.grid(row=3, column=0, columnspan=4, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        main_frame.rowconfigure(3, weight=1)
        
        # Field listbox with scrollbar
        self.field_listbox = tk.Listbox(field_frame, selectmode=tk.MULTIPLE, height=15)
        field_scrollbar = ttk.Scrollbar(field_frame, orient=tk.VERTICAL, command=self.field_listbox.yview)
        self.field_listbox.configure(yscrollcommand=field_scrollbar.set)
        
        self.field_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        field_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        field_frame.columnconfigure(0, weight=1)
        field_frame.rowconfigure(0, weight=1)
        
        # Select/Deselect buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=4, pady=5)
        ttk.Button(button_frame, text="Select All", command=self.select_all_fields).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Deselect All", command=self.deselect_all_fields).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Select Common", command=self.select_common_fields).pack(side=tk.LEFT, padx=5)
        
        # Output file section
        ttk.Label(main_frame, text="Output CSV File:").grid(row=5, column=0, sticky=tk.W, pady=(20, 5))
        ttk.Entry(main_frame, textvariable=self.output_file, width=50).grid(row=5, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(main_frame, text="Browse", command=self.browse_output).grid(row=5, column=2, padx=5)
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=6, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=20)
        
        # Convert button
        self.convert_button = ttk.Button(main_frame, text="Convert to CSV", command=self.convert_to_csv, state=tk.DISABLED)
        self.convert_button.grid(row=7, column=0, columnspan=4, pady=10)
        
        # Status text
        self.status_text = scrolledtext.ScrolledText(main_frame, height=5, width=70)
        self.status_text.grid(row=8, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=10)
        
    def browse_input(self):
        filename = filedialog.askopenfilename(
            title="Select JSON file",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            self.input_file.set(filename)
            # Auto-generate output filename
            base = os.path.splitext(filename)[0]
            self.output_file.set(f"{base}_output.csv")
            
    def browse_output(self):
        filename = filedialog.asksaveasfilename(
            title="Save CSV file as",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            self.output_file.set(filename)
            
    def analyze_file(self):
        if not self.input_file.get():
            messagebox.showerror("Error", "Please select an input file first")
            return
            
        self.progress.start()
        self.status_text.delete(1.0, tk.END)
        self.status_text.insert(tk.END, "Analyzing file structure...\n")
        
        # Run analysis in separate thread
        thread = threading.Thread(target=self._analyze_file_thread)
        thread.start()
        
    def _analyze_file_thread(self):
        try:
            fields_set = set()
            self.preview_data = []
            self.total_records = 0
            
            with open(self.input_file.get(), 'r', encoding='utf-8') as file:
                for line_num, line in enumerate(file):
                    if line.strip():
                        try:
                            data = json.loads(line)
                            self.total_records += 1
                            
                            # Collect first few records for preview
                            if len(self.preview_data) < 5:
                                self.preview_data.append(data)
                            
                            # Extract all field paths
                            self._extract_fields(data, fields_set)
                            
                        except json.JSONDecodeError as e:
                            self.root.after(0, self.status_text.insert, tk.END, f"Warning: Line {line_num + 1} is not valid JSON\n")
            
            self.all_fields = sorted(list(fields_set))
            
            # Update GUI in main thread
            self.root.after(0, self._update_after_analysis)
            
        except Exception as e:
            self.root.after(0, messagebox.showerror, "Error", f"Failed to analyze file: {str(e)}")
        finally:
            self.root.after(0, self.progress.stop)
            
    def _extract_fields(self, obj, fields_set, prefix=""):
        """Recursively extract all field paths from nested JSON"""
        if isinstance(obj, dict):
            for key, value in obj.items():
                field_path = f"{prefix}.{key}" if prefix else key
                fields_set.add(field_path)
                if isinstance(value, dict):
                    self._extract_fields(value, fields_set, field_path)
                    
    def _update_after_analysis(self):
        self.info_label.config(text=f"File loaded: {self.total_records} records, {len(self.all_fields)} fields found")
        
        # Update field listbox
        self.field_listbox.delete(0, tk.END)
        for field in self.all_fields:
            self.field_listbox.insert(tk.END, field)
            
        self.status_text.insert(tk.END, f"Analysis complete! Found {self.total_records} records with {len(self.all_fields)} unique fields.\n")
        self.status_text.insert(tk.END, "\nSample fields:\n")
        for field in self.all_fields[:10]:
            self.status_text.insert(tk.END, f"  - {field}\n")
        if len(self.all_fields) > 10:
            self.status_text.insert(tk.END, f"  ... and {len(self.all_fields) - 10} more fields\n")
            
        self.convert_button.config(state=tk.NORMAL)
        self.select_common_fields()
        
    def select_all_fields(self):
        self.field_listbox.select_set(0, tk.END)
        
    def deselect_all_fields(self):
        self.field_listbox.select_clear(0, tk.END)
        
    def select_common_fields(self):
        """Select commonly useful fields"""
        common_patterns = ['id', 'name', 'email', 'created_at', 'updated_at', 'url', 'domain_names', 
                          'billing_id', 'tags', 'service_level', 'client_classification']
        
        self.deselect_all_fields()
        for i, field in enumerate(self.all_fields):
            for pattern in common_patterns:
                if pattern in field.lower() and '._' not in field:  # Skip internal fields starting with _
                    self.field_listbox.select_set(i)
                    break
                    
    def get_nested_value(self, data, field_path):
        """Get value from nested dictionary using dot notation"""
        keys = field_path.split('.')
        value = data
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return ""
        
        # Convert lists/dicts to string representation
        if isinstance(value, (list, dict)):
            return json.dumps(value)
        return value if value is not None else ""
        
    def convert_to_csv(self):
        selected_indices = self.field_listbox.curselection()
        if not selected_indices:
            messagebox.showerror("Error", "Please select at least one field to export")
            return
            
        self.selected_fields = [self.all_fields[i] for i in selected_indices]
        
        if not self.output_file.get():
            messagebox.showerror("Error", "Please specify an output file")
            return
            
        self.progress.start()
        self.convert_button.config(state=tk.DISABLED)
        self.status_text.delete(1.0, tk.END)
        self.status_text.insert(tk.END, "Converting to CSV...\n")
        
        # Run conversion in separate thread
        thread = threading.Thread(target=self._convert_thread)
        thread.start()
        
    def _convert_thread(self):
        try:
            records_written = 0
            
            with open(self.input_file.get(), 'r', encoding='utf-8') as infile, \
                 open(self.output_file.get(), 'w', newline='', encoding='utf-8') as outfile:
                
                writer = csv.DictWriter(outfile, fieldnames=self.selected_fields)
                writer.writeheader()
                
                for line_num, line in enumerate(infile):
                    if line.strip():
                        try:
                            data = json.loads(line)
                            row = {}
                            for field in self.selected_fields:
                                row[field] = self.get_nested_value(data, field)
                            writer.writerow(row)
                            records_written += 1
                            
                            if records_written % 1000 == 0:
                                self.root.after(0, self.status_text.insert, tk.END, f"Processed {records_written} records...\n")
                                self.root.after(0, self.status_text.see, tk.END)
                                
                        except json.JSONDecodeError:
                            pass  # Skip invalid lines
                            
            self.root.after(0, self._conversion_complete, records_written)
            
        except Exception as e:
            self.root.after(0, messagebox.showerror, "Error", f"Conversion failed: {str(e)}")
        finally:
            self.root.after(0, self.progress.stop)
            self.root.after(0, self.convert_button.config, {'state': tk.NORMAL})
            
    def _conversion_complete(self, records_written):
        self.status_text.insert(tk.END, f"\nConversion complete! {records_written} records written to:\n{self.output_file.get()}\n")
        messagebox.showinfo("Success", f"Successfully converted {records_written} records to CSV!")


def main():
    root = tk.Tk()
    app = JSONtoCSVConverter(root)
    root.mainloop()


if __name__ == "__main__":
    main()