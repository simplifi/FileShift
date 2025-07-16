#!/usr/bin/env python3
"""
JSON to CSV Converter - Standalone App
Can be packaged into a .app bundle with PyInstaller
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import csv
import os
import threading
from pathlib import Path


class JSONtoCSVApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("JSON to CSV Converter")
        self.root.geometry("900x700")
        
        # Make it look more native on macOS
        self.root.tk.call('tk', 'scaling', 1.5)
        
        # Variables
        self.input_file = None
        self.fields = []
        self.selected_fields = set()
        self.total_records = 0
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        
        # Title
        title = ttk.Label(main_frame, text="JSON to CSV Converter", 
                         font=('Helvetica', 24, 'bold'))
        title.grid(row=0, column=0, pady=(0, 20))
        
        # Drop zone
        self.drop_frame = ttk.LabelFrame(main_frame, text="Step 1: Select File", padding="20")
        self.drop_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=10)
        
        self.drop_label = ttk.Label(self.drop_frame, 
                                   text="Drag & drop your JSON file here\nor click to browse",
                                   font=('Helvetica', 14))
        self.drop_label.pack(pady=20)
        
        ttk.Button(self.drop_frame, text="Browse for JSON file", 
                  command=self.browse_file).pack()
        
        # File info
        self.info_frame = ttk.LabelFrame(main_frame, text="File Information", padding="10")
        self.info_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=10)
        self.info_frame.grid_remove()  # Hidden initially
        
        self.info_label = ttk.Label(self.info_frame, text="")
        self.info_label.pack()
        
        # Field selection
        self.field_frame = ttk.LabelFrame(main_frame, text="Step 2: Select Fields", padding="10")
        self.field_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        self.field_frame.grid_remove()  # Hidden initially
        main_frame.rowconfigure(3, weight=1)
        
        # Buttons for field selection
        button_frame = ttk.Frame(self.field_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(button_frame, text="Select All", 
                  command=self.select_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Select None", 
                  command=self.select_none).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Select Common", 
                  command=self.select_common).pack(side=tk.LEFT, padx=5)
        
        # Field list with scrollbar
        list_frame = ttk.Frame(self.field_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.field_listbox = tk.Listbox(list_frame, selectmode=tk.MULTIPLE,
                                       yscrollcommand=scrollbar.set)
        self.field_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.field_listbox.yview)
        
        # Convert button
        self.convert_button = ttk.Button(main_frame, text="Convert to CSV", 
                                        command=self.convert_to_csv,
                                        state=tk.DISABLED)
        self.convert_button.grid(row=4, column=0, pady=20)
        
        # Progress
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=(0, 20))
        self.progress.grid_remove()
        
        # Status
        self.status_label = ttk.Label(main_frame, text="Ready to convert JSON to CSV", 
                                     font=('Helvetica', 12))
        self.status_label.grid(row=6, column=0)
        
        # Enable drag and drop
        self.setup_drag_drop()
        
    def setup_drag_drop(self):
        """Enable drag and drop on macOS"""
        try:
            self.root.tk.call('tk::mac::OpenDocument', self.drop_file)
        except:
            pass  # Drag and drop may not work in all environments
            
    def drop_file(self, filename):
        """Handle dropped file"""
        if filename.endswith('.json'):
            self.load_file(filename)
            
    def browse_file(self):
        """Open file browser"""
        filename = filedialog.askopenfilename(
            title="Select JSON file",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            self.load_file(filename)
            
    def load_file(self, filename):
        """Load and analyze JSON file"""
        self.input_file = filename
        self.status_label.config(text=f"Loading {os.path.basename(filename)}...")
        self.progress.grid()
        self.progress.start()
        
        # Run analysis in background thread
        thread = threading.Thread(target=self.analyze_file)
        thread.daemon = True
        thread.start()
        
    def analyze_file(self):
        """Analyze JSON structure in background"""
        try:
            fields_set = set()
            self.total_records = 0
            
            with open(self.input_file, 'r', encoding='utf-8') as file:
                for line in file:
                    if line.strip():
                        try:
                            data = json.loads(line)
                            self.total_records += 1
                            self._extract_fields(data, fields_set)
                        except json.JSONDecodeError:
                            pass
                            
            self.fields = sorted(list(fields_set))
            
            # Update UI in main thread
            self.root.after(0, self.analysis_complete)
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to analyze file: {str(e)}"))
            self.root.after(0, self.progress.stop)
            self.root.after(0, self.progress.grid_remove)
            
    def _extract_fields(self, obj, fields_set, prefix=""):
        """Recursively extract field paths"""
        if isinstance(obj, dict):
            for key, value in obj.items():
                field_path = f"{prefix}.{key}" if prefix else key
                fields_set.add(field_path)
                if isinstance(value, dict):
                    self._extract_fields(value, fields_set, field_path)
                    
    def analysis_complete(self):
        """Update UI after analysis"""
        self.progress.stop()
        self.progress.grid_remove()
        
        # Show file info
        self.info_frame.grid()
        self.info_label.config(
            text=f"File: {os.path.basename(self.input_file)}\n"
                 f"Records: {self.total_records:,}\n"
                 f"Fields: {len(self.fields)}"
        )
        
        # Show field selection
        self.field_frame.grid()
        self.field_listbox.delete(0, tk.END)
        for field in self.fields:
            self.field_listbox.insert(tk.END, field)
            
        # Enable convert button
        self.convert_button.config(state=tk.NORMAL)
        
        # Auto-select common fields
        self.select_common()
        
        self.status_label.config(text="Select fields and click Convert")
        
    def select_all(self):
        """Select all fields"""
        self.field_listbox.select_set(0, tk.END)
        
    def select_none(self):
        """Deselect all fields"""
        self.field_listbox.select_clear(0, tk.END)
        
    def select_common(self):
        """Select commonly useful fields"""
        common_patterns = ['id', 'name', 'email', 'created_at', 'updated_at', 
                          'url', 'domain_names', 'billing_id', 'tags', 
                          'service_level', 'client_classification']
        
        self.select_none()
        for i, field in enumerate(self.fields):
            for pattern in common_patterns:
                if pattern in field.lower() and '._' not in field:
                    self.field_listbox.select_set(i)
                    break
                    
    def get_nested_value(self, data, field_path):
        """Extract nested value from dict"""
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
        
    def convert_to_csv(self):
        """Convert JSON to CSV"""
        selected_indices = self.field_listbox.curselection()
        if not selected_indices:
            messagebox.showerror("Error", "Please select at least one field")
            return
            
        selected_fields = [self.fields[i] for i in selected_indices]
        
        # Ask for output file
        output_file = filedialog.asksaveasfilename(
            title="Save CSV as",
            defaultextension=".csv",
            initialfile=Path(self.input_file).stem + "_output.csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if not output_file:
            return
            
        self.progress.grid()
        self.progress.start()
        self.status_label.config(text="Converting to CSV...")
        self.convert_button.config(state=tk.DISABLED)
        
        # Run conversion in background
        thread = threading.Thread(target=self.do_conversion, 
                                args=(selected_fields, output_file))
        thread.daemon = True
        thread.start()
        
    def do_conversion(self, selected_fields, output_file):
        """Perform the actual conversion"""
        try:
            records_written = 0
            
            with open(self.input_file, 'r', encoding='utf-8') as infile, \
                 open(output_file, 'w', newline='', encoding='utf-8') as outfile:
                
                writer = csv.DictWriter(outfile, fieldnames=selected_fields)
                writer.writeheader()
                
                for line in infile:
                    if line.strip():
                        try:
                            data = json.loads(line)
                            row = {}
                            for field in selected_fields:
                                row[field] = self.get_nested_value(data, field)
                            writer.writerow(row)
                            records_written += 1
                        except json.JSONDecodeError:
                            pass
                            
            # Update UI in main thread
            self.root.after(0, self.conversion_complete, records_written, output_file)
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Conversion failed: {str(e)}"))
            self.root.after(0, self.reset_ui)
            
    def conversion_complete(self, records_written, output_file):
        """Handle successful conversion"""
        self.progress.stop()
        self.progress.grid_remove()
        self.convert_button.config(state=tk.NORMAL)
        
        self.status_label.config(
            text=f"Success! Converted {records_written:,} records to CSV"
        )
        
        result = messagebox.askyesno(
            "Success", 
            f"Converted {records_written:,} records to:\n{output_file}\n\n"
            "Would you like to open the file?"
        )
        
        if result:
            os.system(f'open "{output_file}"')
            
    def reset_ui(self):
        """Reset UI state"""
        self.progress.stop()
        self.progress.grid_remove()
        self.convert_button.config(state=tk.NORMAL)
        
    def run(self):
        """Start the application"""
        self.root.mainloop()


def main():
    app = JSONtoCSVApp()
    app.run()


if __name__ == "__main__":
    main()