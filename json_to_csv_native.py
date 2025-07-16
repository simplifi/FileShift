#!/usr/bin/env python3
"""
JSON to CSV Converter - Native macOS Version
Uses native macOS dialogs via osascript - no tkinter required!
Full GUI experience using system-provided interface elements.
"""

import json
import csv
import os
import sys
import subprocess
from pathlib import Path


def show_dialog(message, buttons=["OK"]):
    """Show native macOS dialog"""
    button_str = ', '.join([f'"{b}"' for b in buttons])
    script = f'''
    tell application "System Events"
        activate
        display dialog "{message}" buttons {{{button_str}}} default button 1
        return button returned of result
    end tell
    '''
    try:
        result = subprocess.run(['osascript', '-e', script], 
                              capture_output=True, text=True)
        return result.stdout.strip()
    except:
        return None


def get_file_dialog(prompt="Select file"):
    """Native macOS file picker - accepts any file type"""
    script = f'''
    tell application "System Events"
        activate
        set theFile to choose file with prompt "{prompt}"
        return POSIX path of theFile
    end tell
    '''
    try:
        result = subprocess.run(['osascript', '-e', script], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
    except:
        pass
    return None


def save_file_dialog(prompt="Save as", default_name="output.csv"):
    """Native macOS save dialog"""
    script = f'''
    tell application "System Events"
        activate
        set theFile to choose file name with prompt "{prompt}" default name "{default_name}"
        return POSIX path of theFile
    end tell
    '''
    try:
        result = subprocess.run(['osascript', '-e', script], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            path = result.stdout.strip()
            if not path.endswith('.csv'):
                path += '.csv'
            return path
    except:
        pass
    return None


def show_notification(title, message):
    """macOS notification"""
    script = f'display notification "{message}" with title "{title}"'
    subprocess.run(['osascript', '-e', script])


def analyze_json(filepath):
    """Extract all unique fields from NDJSON file"""
    fields_set = set()
    total_records = 0
    
    print(f"Analyzing {filepath}...")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:
                    data = json.loads(line)
                    total_records += 1
                    extract_fields(data, fields_set)
                except json.JSONDecodeError:
                    continue
    
    print(f"Found {total_records} records with {len(fields_set)} fields")
    return sorted(list(fields_set)), total_records


def extract_fields(obj, fields_set, prefix=""):
    """Recursively extract field paths"""
    if isinstance(obj, dict):
        for key, value in obj.items():
            field_path = f"{prefix}.{key}" if prefix else key
            fields_set.add(field_path)
            if isinstance(value, dict):
                extract_fields(value, fields_set, field_path)


def select_fields_dialog(all_fields):
    """Field selection using native dialog"""
    # Auto-select common fields
    common_patterns = ['id', 'name', 'email', 'created_at', 'updated_at', 
                      'url', 'domain_names', 'billing_id', 'tags', 
                      'service_level', 'client_classification']
    
    suggested = []
    for field in all_fields:
        for pattern in common_patterns:
            if pattern in field.lower() and '._' not in field:
                suggested.append(field)
                break
    
    # Create a simple selection dialog
    field_list = "\\n".join([f"• {f}" for f in suggested[:15]])
    
    response = show_dialog(
        f"Found {len(all_fields)} fields. Auto-selected {len(suggested)} common fields:\\n\\n{field_list}\\n\\nProceed with these fields?",
        ["Use Selected", "Use All Fields", "Cancel"]
    )
    
    if response == "Use Selected":
        return suggested
    elif response == "Use All Fields":
        return all_fields
    else:
        return None


def get_nested_value(data, field_path):
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


def convert_to_csv(input_file, output_file, fields):
    """Convert NDJSON to CSV"""
    records_written = 0
    
    print(f"Converting to {output_file}...")
    
    with open(input_file, 'r', encoding='utf-8') as infile, \
         open(output_file, 'w', newline='', encoding='utf-8') as outfile:
        
        writer = csv.DictWriter(outfile, fieldnames=fields)
        writer.writeheader()
        
        for line in infile:
            if line.strip():
                try:
                    data = json.loads(line)
                    row = {}
                    for field in fields:
                        row[field] = get_nested_value(data, field)
                    writer.writerow(row)
                    records_written += 1
                    
                    if records_written % 1000 == 0:
                        print(f"  Processed {records_written} records...")
                        
                except json.JSONDecodeError:
                    continue
    
    print(f"Successfully converted {records_written} records")
    return records_written


def main():
    print("JSON to CSV Converter")
    print("=" * 50)
    
    # Get input file
    input_file = get_file_dialog("Select JSON file to convert")
    if not input_file:
        print("No file selected")
        return
    
    # Analyze file
    try:
        fields, total_records = analyze_json(input_file)
    except Exception as e:
        show_dialog(f"Error analyzing file: {str(e)}")
        return
    
    # Select fields
    selected_fields = select_fields_dialog(fields)
    if not selected_fields:
        print("Cancelled")
        return
    
    # Get output file
    default_name = Path(input_file).stem + "_output.csv"
    output_file = save_file_dialog("Save CSV as", default_name)
    if not output_file:
        print("No output file selected")
        return
    
    # Convert
    try:
        records = convert_to_csv(input_file, output_file, selected_fields)
        
        show_notification("JSON to CSV Converter", 
                         f"Converted {records} records successfully!")
        
        # Ask to open file
        response = show_dialog(
            f"Successfully converted {records} records to CSV.\\n\\nOpen the file?",
            ["Open", "Done"]
        )
        
        if response == "Open":
            subprocess.run(['open', output_file])
            
    except Exception as e:
        show_dialog(f"Error converting file: {str(e)}")


if __name__ == "__main__":
    main()