#!/usr/bin/env python3
"""
JSON to CSV Converter (Multi-File) - Native macOS Version
Uses osascript for sophisticated multi-file batch processing
Handles schema analysis and smart field merging strategies
"""

import json
import csv
import os
import sys
import subprocess
from pathlib import Path
from collections import defaultdict, Counter


def show_dialog(message, buttons=["OK"]):
    """Show native macOS dialog"""
    button_str = ', '.join([f'"{b}"' for b in buttons])
    # Escape quotes and newlines in message
    escaped_message = message.replace('"', '\\"').replace('\n', '\\n')
    script = f'''
    tell application "System Events"
        activate
        display dialog "{escaped_message}" buttons {{{button_str}}} default button 1
        return button returned of result
    end tell
    '''
    try:
        result = subprocess.run(['osascript', '-e', script], 
                              capture_output=True, text=True)
        return result.stdout.strip()
    except:
        return None


def choose_multiple_files():
    """Native macOS multiple file picker"""
    script = '''
    tell application "System Events"
        activate
        set theFiles to choose file with prompt "Select JSON files to convert" with multiple selections allowed
        set filePaths to {}
        repeat with aFile in theFiles
            set end of filePaths to POSIX path of aFile
        end repeat
        return filePaths
    end tell
    '''
    try:
        result = subprocess.run(['osascript', '-e', script], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            # Parse the returned list
            paths_str = result.stdout.strip()
            if paths_str:
                # AppleScript returns comma-separated paths
                paths = [p.strip() for p in paths_str.split(',')]
                return [p for p in paths if p.endswith('.json')]
    except:
        pass
    return []


def show_progress(message, current=None, total=None):
    """Show progress notification"""
    if current and total:
        progress_msg = f"{message} ({current}/{total})"
    else:
        progress_msg = message
    
    script = f'display notification "{progress_msg}" with title "JSON to CSV Converter"'
    subprocess.run(['osascript', '-e', script], capture_output=True)


def analyze_files_schema(file_paths):
    """Analyze schema across multiple files"""
    print("Step 2: Schema Analysis")
    print("=" * 50)
    
    all_fields = set()
    file_schemas = {}
    file_record_counts = {}
    field_frequency = Counter()
    
    show_progress("Analyzing file schemas...")
    
    for i, file_path in enumerate(file_paths):
        show_progress("Analyzing schemas", i+1, len(file_paths))
        
        fields_set = set()
        record_count = 0
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        try:
                            data = json.loads(line)
                            record_count += 1
                            extract_fields(data, fields_set)
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            continue
        
        file_schemas[file_path] = sorted(list(fields_set))
        file_record_counts[file_path] = record_count
        all_fields.update(fields_set)
        
        # Count field frequency across files
        for field in fields_set:
            field_frequency[field] += 1
        
        print(f"  {Path(file_path).name}: {record_count} records, {len(fields_set)} fields")
    
    total_records = sum(file_record_counts.values())
    total_unique_fields = len(all_fields)
    
    print(f"\nFiles have varying schemas ({total_unique_fields} unique fields across {len(file_paths)} files, {total_records} total records)")
    
    return file_schemas, file_record_counts, all_fields, field_frequency


def extract_fields(obj, fields_set, prefix=""):
    """Recursively extract field paths"""
    if isinstance(obj, dict):
        for key, value in obj.items():
            field_path = f"{prefix}.{key}" if prefix else key
            fields_set.add(field_path)
            if isinstance(value, dict):
                extract_fields(value, fields_set, field_path)


def choose_merge_strategy(file_schemas, file_record_counts, all_fields, field_frequency):
    """Present field selection strategy options"""
    print("\nStep 3: Field Selection")
    print("=" * 50)
    
    num_files = len(file_schemas)
    
    # Calculate strategy options
    smart_auto_threshold = max(1, int(0.7 * num_files))  # 70% of files
    smart_auto_fields = [field for field, count in field_frequency.items() 
                        if count >= smart_auto_threshold]
    
    common_fields = [field for field, count in field_frequency.items() 
                    if count == num_files]
    
    # Find most complete file
    richest_file = max(file_schemas.keys(), key=lambda f: len(file_schemas[f]))
    richest_fields = file_schemas[richest_file]
    
    # Present options
    strategies = [
        f"Merge with Smart Auto - Fields in {smart_auto_threshold}+ files ({len(smart_auto_fields)} fields)",
        f"Merge with All Available - Union of all fields ({len(all_fields)} fields)",
        f"Merge with Common Only - Fields in ALL files ({len(common_fields)} fields)",
        f"Merge with Most Complete File - Use '{Path(richest_file).name}' ({len(richest_fields)} fields)",
        "Keep Files Separate - Individual CSVs with own fields"
    ]
    
    strategy_text = "\\n".join([f"{i+1}. {s}" for i, s in enumerate(strategies)])
    
    message = f"Files have different schemas. Choose field selection strategy:\\n\\n{strategy_text}"
    
    response = show_dialog(message, ["1", "2", "3", "4", "5", "Cancel"])
    
    if response == "Cancel":
        return None, None
    
    strategy_map = {
        "1": ("smart_auto", smart_auto_fields),
        "2": ("all_available", list(all_fields)),
        "3": ("common_only", common_fields),
        "4": ("most_complete", richest_fields),
        "5": ("separate", None)
    }
    
    return strategy_map.get(response, (None, None))


def save_directory_dialog():
    """Choose output directory"""
    script = '''
    tell application "System Events"
        activate
        set theFolder to choose folder with prompt "Select output directory for CSV files"
        return POSIX path of theFolder
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


def convert_files(file_paths, strategy, selected_fields, output_dir):
    """Convert files based on strategy"""
    print("\nStep 4: Convert to CSV")
    print("=" * 50)
    
    if strategy == "separate":
        return convert_files_separate(file_paths, output_dir)
    else:
        return convert_files_merged(file_paths, selected_fields, output_dir, strategy)


def convert_files_separate(file_paths, output_dir):
    """Convert each file separately with its own schema"""
    results = []
    
    for i, file_path in enumerate(file_paths):
        show_progress("Converting files", i+1, len(file_paths))
        
        # Analyze this file's schema
        fields_set = set()
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        data = json.loads(line)
                        extract_fields(data, fields_set)
                    except json.JSONDecodeError:
                        continue
        
        file_fields = sorted(list(fields_set))
        
        # Convert file
        input_name = Path(file_path).stem
        output_file = os.path.join(output_dir, f"{input_name}.csv")
        
        records_written = 0
        with open(file_path, 'r', encoding='utf-8') as infile, \
             open(output_file, 'w', newline='', encoding='utf-8') as outfile:
            
            writer = csv.DictWriter(outfile, fieldnames=file_fields)
            writer.writeheader()
            
            for line in infile:
                if line.strip():
                    try:
                        data = json.loads(line)
                        row = {}
                        for field in file_fields:
                            row[field] = get_nested_value(data, field)
                        writer.writerow(row)
                        records_written += 1
                    except json.JSONDecodeError:
                        continue
        
        results.append(f"{Path(file_path).name}: {records_written} records converted")
        print(f"  ✓ {Path(file_path).name}: {records_written} records converted")
    
    return results


def convert_files_merged(file_paths, selected_fields, output_dir, strategy):
    """Convert all files into single CSV with merged schema"""
    output_file = os.path.join(output_dir, f"merged_{strategy}.csv")
    
    total_records = 0
    results = []
    
    with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=selected_fields)
        writer.writeheader()
        
        for i, file_path in enumerate(file_paths):
            show_progress("Converting files", i+1, len(file_paths))
            
            file_records = 0
            with open(file_path, 'r', encoding='utf-8') as infile:
                for line in infile:
                    if line.strip():
                        try:
                            data = json.loads(line)
                            row = {}
                            for field in selected_fields:
                                row[field] = get_nested_value(data, field)
                            writer.writerow(row)
                            file_records += 1
                            total_records += 1
                        except json.JSONDecodeError:
                            continue
            
            results.append(f"{Path(file_path).name}: {file_records} records converted")
            print(f"  ✓ {Path(file_path).name}: {file_records} records converted")
    
    print(f"\nBatch conversion complete: {len(file_paths)} files, {total_records} total records")
    return results


def show_main_interface():
    """Show the main multi-step interface"""
    
    # Show welcome and workflow
    workflow_text = """JSON to CSV Converter (Multi-File)

This tool will guide you through:

Step 1: Select JSON Files
Step 2: Schema Analysis  
Step 3: Field Selection Strategy
Step 4: Convert to CSV

Ready to start?"""
    
    response = show_dialog(workflow_text, ["Start Workflow", "Cancel"])
    
    if response != "Start Workflow":
        return
    
    # Now begin the workflow
    run_workflow()


def run_workflow():
    """Run the complete workflow"""
    print("JSON to CSV Converter (Multi-File)")
    print("=" * 50)
    
    # Step 1: Select JSON Files
    print("Step 1: Select JSON Files")
    print("=" * 50)
    
    file_paths = choose_multiple_files()
    if not file_paths:
        print("No files selected")
        return
    
    print(f"\n{len(file_paths)} files selected:")
    for path in file_paths:
        print(f"  {Path(path).name}")
    
    # Step 2: Schema Analysis
    file_schemas, file_record_counts, all_fields, field_frequency = analyze_files_schema(file_paths)
    
    if not file_schemas:
        show_dialog("No valid JSON files found")
        return
    
    # Step 3: Field Selection Strategy
    strategy, selected_fields = choose_merge_strategy(file_schemas, file_record_counts, all_fields, field_frequency)
    
    if strategy is None:
        print("Cancelled")
        return
    
    print(f"\nStrategy: {strategy}")
    if selected_fields:
        print(f"Fields: {len(selected_fields)} selected")
    
    # Choose output directory
    output_dir = save_directory_dialog()
    if not output_dir:
        print("No output directory selected")
        return
    
    # Step 4: Convert
    try:
        results = convert_files(file_paths, strategy, selected_fields, output_dir)
        
        # Show completion
        results_text = "\\n".join(results)
        show_dialog(f"Batch conversion complete!\\n\\n{results_text}")
        
        # Ask to open output directory
        response = show_dialog("Open output directory?", ["Open", "Done"])
        if response == "Open":
            subprocess.run(['open', output_dir])
            
    except Exception as e:
        show_dialog(f"Error during conversion: {str(e)}")


def main():
    """Main entry point"""
    show_main_interface()


if __name__ == "__main__":
    main()