#!/usr/bin/env python3
"""
JSON to CSV Converter (Multi-File) - Native Cocoa Interface
Recreates the exact interface shown in the screenshot
"""

import json
import csv
import os
import sys
from pathlib import Path
from collections import Counter
import threading

try:
    import Cocoa
    import Foundation
    from PyObjC import objc
except ImportError:
    print("Error: PyObjC not available. Try running with system Python:")
    print("/usr/bin/python3 json_to_csv_multifile_cocoa.py")
    exit(1)


class MultiFileConverter(Cocoa.NSObject):
    
    def init(self):
        self = objc.super(MultiFileConverter, self).init()
        if self is None:
            return None
        
        # Data
        self.selected_files = []
        self.file_schemas = {}
        self.all_fields = set()
        self.field_frequency = Counter()
        self.selected_strategy = "separate"
        self.selected_fields = []
        
        return self
    
    def applicationDidFinishLaunching_(self, notification):
        """Set up the main window when app launches"""
        self.setupWindow()
    
    def setupWindow(self):
        """Create the main application window matching the screenshot"""
        # Create main window - larger to match screenshot
        frame = Foundation.NSMakeRect(0, 0, 1200, 800)
        style = (Cocoa.NSTitledWindowMask | 
                Cocoa.NSClosableWindowMask | 
                Cocoa.NSMiniaturizableWindowMask | 
                Cocoa.NSResizableWindowMask)
        
        self.window = Cocoa.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            frame, style, Cocoa.NSBackingStoreBuffered, False)
        
        self.window.setTitle_("JSON to CSV Converter (Multi-File)")
        self.window.center()
        
        # Create content view
        content_view = Cocoa.NSView.alloc().initWithFrame_(frame)
        self.window.setContentView_(content_view)
        
        # Title
        title_label = Cocoa.NSTextField.alloc().initWithFrame_(
            Foundation.NSMakeRect(50, 730, 1100, 40))
        title_label.setStringValue_("JSON to CSV Converter (Multi-File)")
        title_label.setBezeled_(False)
        title_label.setDrawsBackground_(False)
        title_label.setEditable_(False)
        title_label.setSelectable_(False)
        title_label.setFont_(Cocoa.NSFont.boldSystemFontOfSize_(24))
        title_label.setAlignment_(Cocoa.NSCenterTextAlignment)
        content_view.addSubview_(title_label)
        
        # Step 1: Select JSON Files
        self.setupStep1(content_view)
        
        # Step 2: Schema Analysis  
        self.setupStep2(content_view)
        
        # Step 3: Field Selection
        self.setupStep3(content_view)
        
        # Step 4: Convert to CSV
        self.setupStep4(content_view)
        
        # Status Log
        self.setupStatusLog(content_view)
        
        # Show window
        self.window.makeKeyAndOrderFront_(None)
    
    def setupStep1(self, content_view):
        """Step 1: Select JSON Files"""
        y_pos = 620
        
        # Step 1 Box
        step1_box = Cocoa.NSBox.alloc().initWithFrame_(
            Foundation.NSMakeRect(30, y_pos - 100, 1140, 120))
        step1_box.setTitle_("Step 1: Select JSON Files")
        step1_box.setTitlePosition_(Cocoa.NSAtTop)
        content_view.addSubview_(step1_box)
        
        # Browse button (green like in screenshot)
        self.browse_button = Cocoa.NSButton.alloc().initWithFrame_(
            Foundation.NSMakeRect(50, y_pos - 60, 200, 35))
        self.browse_button.setTitle_("Browse for JSON Files")
        self.browse_button.setTarget_(self)
        self.browse_button.setAction_("browseFiles:")
        self.browse_button.setBezelStyle_(Cocoa.NSRoundedBezelStyle)
        content_view.addSubview_(self.browse_button)
        
        # File list area
        self.file_list_view = Cocoa.NSTextView.alloc().initWithFrame_(
            Foundation.NSMakeRect(280, y_pos - 90, 860, 80))
        self.file_list_view.setEditable_(False)
        self.file_list_view.setString_("No files selected")
        content_view.addSubview_(self.file_list_view)
        
        # Files count label
        self.files_count_label = Cocoa.NSTextField.alloc().initWithFrame_(
            Foundation.NSMakeRect(50, y_pos - 95, 200, 20))
        self.files_count_label.setStringValue_("0 files selected")
        self.files_count_label.setBezeled_(False)
        self.files_count_label.setDrawsBackground_(False)
        self.files_count_label.setEditable_(False)
        content_view.addSubview_(self.files_count_label)
    
    def setupStep2(self, content_view):
        """Step 2: Schema Analysis"""
        y_pos = 480
        
        # Step 2 Box
        step2_box = Cocoa.NSBox.alloc().initWithFrame_(
            Foundation.NSMakeRect(30, y_pos - 80, 1140, 100))
        step2_box.setTitle_("Step 2: Schema Analysis")
        step2_box.setTitlePosition_(Cocoa.NSAtTop)
        content_view.addSubview_(step2_box)
        
        # Analysis results
        self.analysis_label = Cocoa.NSTextField.alloc().initWithFrame_(
            Foundation.NSMakeRect(50, y_pos - 60, 1080, 40))
        self.analysis_label.setStringValue_("⚠️ Files have varying schemas (0 unique fields across 0 files, 0 total records)")
        self.analysis_label.setBezeled_(False)
        self.analysis_label.setDrawsBackground_(False)
        self.analysis_label.setEditable_(False)
        content_view.addSubview_(self.analysis_label)
    
    def setupStep3(self, content_view):
        """Step 3: Field Selection"""
        y_pos = 350
        
        # Step 3 Box
        step3_box = Cocoa.NSBox.alloc().initWithFrame_(
            Foundation.NSMakeRect(30, y_pos - 180, 1140, 200))
        step3_box.setTitle_("Step 3: Field Selection")
        step3_box.setTitlePosition_(Cocoa.NSAtTop)
        content_view.addSubview_(step3_box)
        
        # Strategy text
        strategy_label = Cocoa.NSTextField.alloc().initWithFrame_(
            Foundation.NSMakeRect(50, y_pos - 40, 500, 20))
        strategy_label.setStringValue_("Files have different schemas. Choose field selection strategy:")
        strategy_label.setBezeled_(False)
        strategy_label.setDrawsBackground_(False)
        strategy_label.setEditable_(False)
        content_view.addSubview_(strategy_label)
        
        # Radio buttons for strategies
        self.radio_buttons = []
        strategies = [
            "☑️ Merge with Smart Auto - Fields in 70%+ of files (0 fields)",
            "☑️ Merge with All Available - Union of all fields (0 fields)", 
            "☑️ Merge with Common Only - Fields in ALL files (0 fields)",
            "☑️ Merge with Most Complete File - Use 'file.json' (0 fields)",
            "🔘 Keep Files Separate - Individual CSVs with own fields"
        ]
        
        for i, strategy in enumerate(strategies):
            radio = Cocoa.NSButton.alloc().initWithFrame_(
                Foundation.NSMakeRect(70, y_pos - 70 - (i * 25), 800, 20))
            radio.setTitle_(strategy)
            radio.setButtonType_(Cocoa.NSRadioButton)
            radio.setTarget_(self)
            radio.setAction_("strategyChanged:")
            radio.setTag_(i)
            if i == 4:  # Default to "Keep Files Separate"
                radio.setState_(Cocoa.NSOnState)
            content_view.addSubview_(radio)
            self.radio_buttons.append(radio)
        
        # Strategy dropdown
        strategy_dropdown_label = Cocoa.NSTextField.alloc().initWithFrame_(
            Foundation.NSMakeRect(50, y_pos - 175, 150, 20))
        strategy_dropdown_label.setStringValue_("Strategy for each file:")
        strategy_dropdown_label.setBezeled_(False)
        strategy_dropdown_label.setDrawsBackground_(False)
        strategy_dropdown_label.setEditable_(False)
        content_view.addSubview_(strategy_dropdown_label)
        
        self.strategy_dropdown = Cocoa.NSPopUpButton.alloc().initWithFrame_(
            Foundation.NSMakeRect(210, y_pos - 175, 200, 25))
        self.strategy_dropdown.addItemWithTitle_("Select All Fields (per file)")
        content_view.addSubview_(self.strategy_dropdown)
    
    def setupStep4(self, content_view):
        """Step 4: Convert to CSV"""
        y_pos = 140
        
        # Step 4 Box
        step4_box = Cocoa.NSBox.alloc().initWithFrame_(
            Foundation.NSMakeRect(30, y_pos - 60, 1140, 80))
        step4_box.setTitle_("Step 4: Convert to CSV")
        step4_box.setTitlePosition_(Cocoa.NSAtTop)
        content_view.addSubview_(step4_box)
        
        # Convert button (green like in screenshot)
        self.convert_button = Cocoa.NSButton.alloc().initWithFrame_(
            Foundation.NSMakeRect(50, y_pos - 45, 150, 35))
        self.convert_button.setTitle_("🚀 Convert All Files")
        self.convert_button.setTarget_(self)
        self.convert_button.setAction_("convertFiles:")
        self.convert_button.setBezelStyle_(Cocoa.NSRoundedBezelStyle)
        self.convert_button.setEnabled_(False)
        content_view.addSubview_(self.convert_button)
        
        # Completion indicator
        self.completion_label = Cocoa.NSTextField.alloc().initWithFrame_(
            Foundation.NSMakeRect(220, y_pos - 40, 300, 25))
        self.completion_label.setStringValue_("")
        self.completion_label.setBezeled_(False)
        self.completion_label.setDrawsBackground_(False)
        self.completion_label.setEditable_(False)
        content_view.addSubview_(self.completion_label)
    
    def setupStatusLog(self, content_view):
        """Status Log"""
        y_pos = 60
        
        # Status Log Box
        log_box = Cocoa.NSBox.alloc().initWithFrame_(
            Foundation.NSMakeRect(30, 20, 1140, y_pos))
        log_box.setTitle_("Status Log")
        log_box.setTitlePosition_(Cocoa.NSAtTop)
        content_view.addSubview_(log_box)
        
        # Scrollable text view for log
        scroll_view = Cocoa.NSScrollView.alloc().initWithFrame_(
            Foundation.NSMakeRect(40, 30, 1120, y_pos - 20))
        scroll_view.setHasVerticalScroller_(True)
        scroll_view.setAutohidesScrollers_(True)
        
        self.log_text_view = Cocoa.NSTextView.alloc().initWithFrame_(
            Foundation.NSMakeRect(0, 0, 1100, y_pos - 20))
        self.log_text_view.setEditable_(False)
        self.log_text_view.setFont_(Cocoa.NSFont.fontWithName_size_("Monaco", 10))
        
        scroll_view.setDocumentView_(self.log_text_view)
        content_view.addSubview_(scroll_view)
    
    def logMessage_(self, message):
        """Add message to status log"""
        current_text = self.log_text_view.string()
        timestamp = Foundation.NSDate.date().descriptionWithLocale_(None)[:19]
        new_text = f"{current_text}{timestamp} - {message}\n"
        self.log_text_view.setString_(new_text)
        
        # Scroll to bottom
        range_end = Foundation.NSMakeRange(len(new_text), 0)
        self.log_text_view.scrollRangeToVisible_(range_end)
    
    def browseFiles_(self, sender):
        """Browse for JSON files"""
        panel = Cocoa.NSOpenPanel.openPanel()
        panel.setTitle_("Select JSON Files")
        panel.setAllowedFileTypes_(["json"])
        panel.setCanChooseFiles_(True)
        panel.setCanChooseDirectories_(False)
        panel.setAllowsMultipleSelection_(True)
        
        if panel.runModal() == Cocoa.NSFileHandlingPanelOKButton:
            urls = panel.URLs()
            self.selected_files = [url.path() for url in urls]
            
            # Update file list display
            file_names = [Path(f).name for f in self.selected_files]
            self.file_list_view.setString_("\n".join(file_names))
            
            # Update count
            self.files_count_label.setStringValue_(f"{len(self.selected_files)} files selected")
            
            # Log selection
            self.logMessage_(f"{len(self.selected_files)} files selected")
            
            # Analyze schemas
            self.analyzeSchemas()
    
    def analyzeSchemas(self):
        """Analyze schemas of selected files"""
        self.logMessage_("Analyzing file schemas...")
        
        # Run in background thread
        thread = threading.Thread(target=self.analyzeSchemas_background)
        thread.daemon = True
        thread.start()
    
    def analyzeSchemas_background(self):
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
        Foundation.NSOperationQueue.mainQueue().addOperationWithBlock_(
            lambda: self.updateAnalysisResults(total_records))
    
    def extract_fields(self, obj, fields_set, prefix=""):
        """Recursively extract field paths"""
        if isinstance(obj, dict):
            for key, value in obj.items():
                field_path = f"{prefix}.{key}" if prefix else key
                fields_set.add(field_path)
                if isinstance(value, dict):
                    self.extract_fields(value, fields_set, field_path)
    
    def updateAnalysisResults(self, total_records):
        """Update analysis results in UI"""
        num_files = len(self.selected_files)
        num_fields = len(self.all_fields)
        
        self.analysis_label.setStringValue_(
            f"⚠️ Files have varying schemas ({num_fields} unique fields across {num_files} files, {total_records} total records)")
        
        # Update radio button labels with actual counts
        smart_auto_count = len([f for f, c in self.field_frequency.items() if c >= max(1, int(0.7 * num_files))])
        common_count = len([f for f, c in self.field_frequency.items() if c == num_files])
        
        if self.file_schemas:
            richest_file = max(self.file_schemas.keys(), key=lambda f: len(self.file_schemas[f]))
            richest_count = len(self.file_schemas[richest_file])
            richest_name = Path(richest_file).name
        else:
            richest_count = 0
            richest_name = "file.json"
        
        strategies = [
            f"☑️ Merge with Smart Auto - Fields in 70%+ of files ({smart_auto_count} fields)",
            f"☑️ Merge with All Available - Union of all fields ({num_fields} fields)",
            f"☑️ Merge with Common Only - Fields in ALL files ({common_count} fields)", 
            f"☑️ Merge with Most Complete File - Use '{richest_name}' ({richest_count} fields)",
            "🔘 Keep Files Separate - Individual CSVs with own fields"
        ]
        
        for i, strategy in enumerate(strategies):
            self.radio_buttons[i].setTitle_(strategy)
        
        # Enable convert button
        self.convert_button.setEnabled_(True)
        
        self.logMessage_(f"Schema analysis complete: {num_fields} unique fields found")
    
    def strategyChanged_(self, sender):
        """Handle strategy radio button change"""
        # Uncheck all others
        for radio in self.radio_buttons:
            if radio != sender:
                radio.setState_(Cocoa.NSOffState)
        
        sender.setState_(Cocoa.NSOnState)
        self.selected_strategy = sender.tag()
        
        strategy_names = ["smart_auto", "all_available", "common_only", "most_complete", "separate"]
        self.logMessage_(f"Strategy selected: {strategy_names[self.selected_strategy]}")
    
    def convertFiles_(self, sender):
        """Convert files to CSV"""
        if not self.selected_files:
            return
        
        # Choose output directory
        panel = Cocoa.NSOpenPanel.openPanel()
        panel.setTitle_("Select Output Directory")
        panel.setCanChooseFiles_(False)
        panel.setCanChooseDirectories_(True)
        panel.setAllowsMultipleSelection_(False)
        
        if panel.runModal() != Cocoa.NSFileHandlingPanelOKButton:
            return
        
        output_dir = panel.URL().path()
        
        # Disable convert button during processing
        self.convert_button.setEnabled_(False)
        
        # Run conversion in background
        thread = threading.Thread(target=self.performConversion, args=(output_dir,))
        thread.daemon = True
        thread.start()
    
    def performConversion(self, output_dir):
        """Perform the actual conversion"""
        try:
            total_records = 0
            
            for i, file_path in enumerate(self.selected_files):
                Foundation.NSOperationQueue.mainQueue().addOperationWithBlock_(
                    lambda: self.logMessage_(f"Converting {Path(file_path).name}..."))
                
                # Convert individual file
                records = self.convertSingleFile(file_path, output_dir)
                total_records += records
                
                Foundation.NSOperationQueue.mainQueue().addOperationWithBlock_(
                    lambda f=file_path, r=records: self.logMessage_(f"✅ {Path(f).name}: {r} records converted"))
            
            # Update UI on completion
            Foundation.NSOperationQueue.mainQueue().addOperationWithBlock_(
                lambda: self.conversionComplete(total_records, len(self.selected_files)))
            
        except Exception as e:
            Foundation.NSOperationQueue.mainQueue().addOperationWithBlock_(
                lambda: self.logMessage_(f"❌ Conversion failed: {str(e)}"))
    
    def convertSingleFile(self, file_path, output_dir):
        """Convert a single file"""
        # Get fields for this file
        if self.selected_strategy == 4:  # separate
            fields = self.file_schemas.get(file_path, [])
        else:
            # Use merged strategy fields (simplified for now)
            fields = list(self.all_fields)
        
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
    
    def conversionComplete(self, total_records, num_files):
        """Handle conversion completion"""
        self.completion_label.setStringValue_("✅ Batch conversion complete!")
        self.convert_button.setEnabled_(True)
        self.logMessage_(f"Batch conversion complete: {num_files} files, {total_records} total records")
        
        # Show completion alert
        alert = Cocoa.NSAlert.alloc().init()
        alert.setMessageText_("Conversion Complete")
        alert.setInformativeText_(f"Successfully converted {num_files} files with {total_records} total records")
        alert.addButtonWithTitle_("OK")
        alert.runModal()


def main():
    """Main application entry point"""
    app = Cocoa.NSApplication.sharedApplication()
    
    # Create app delegate
    delegate = MultiFileConverter.alloc().init()
    app.setDelegate_(delegate)
    
    # Run the app
    app.run()


if __name__ == "__main__":
    main()