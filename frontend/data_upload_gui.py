"""
Rate Edge - Data Upload GUI
GUI interface for uploading daily rates
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
import os
from data_upload_handler import RateUploadHandler


class DataUploadTab:
    """Data Upload tab for the Rate Edge application"""
    
    def __init__(self, parent_notebook, database_manager):
        """Initialize the upload tab"""
        self.db_manager = database_manager
        self.upload_handler = RateUploadHandler(database_manager)
        self.selected_file = None
        
        # Create main frame
        self.frame = ttk.Frame(parent_notebook)
        parent_notebook.add(self.frame, text="📤 Upload Data")
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface"""
        
        # Main container with padding
        main_container = ttk.Frame(self.frame)
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ttk.Label(
            main_container,
            text="📊 Daily Rates Upload Tool",
            font=("Segoe UI", 16, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Upload section
        self.create_upload_section(main_container)
        
        # Preview section
        self.create_preview_section(main_container)
        
        # Results section
        self.create_results_section(main_container)
        
        # Template download section
        self.create_template_section(main_container)
    
    def create_upload_section(self, parent):
        """Create the file upload section"""
        
        upload_frame = ttk.LabelFrame(parent, text="1. Select and Upload File", padding=15)
        upload_frame.pack(fill="x", pady=(0, 15))
        
        # Rate type selection
        type_frame = ttk.Frame(upload_frame)
        type_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(type_frame, text="Rate Type:", font=("Segoe UI", 10, "bold")).pack(side="left", padx=(0, 10))
        
        self.rate_type_var = tk.StringVar(value="benchmark")
        
        ttk.Radiobutton(
            type_frame,
            text="Benchmark Rates (BBSW, CDOR, etc.)",
            variable=self.rate_type_var,
            value="benchmark"
        ).pack(side="left", padx=10)
        
        ttk.Radiobutton(
            type_frame,
            text="Swap Rates",
            variable=self.rate_type_var,
            value="swap"
        ).pack(side="left", padx=10)
        
        ttk.Radiobutton(
            type_frame,
            text="OIS Rates",
            variable=self.rate_type_var,
            value="ois"
        ).pack(side="left", padx=10)
        
        # File selection
        file_frame = ttk.Frame(upload_frame)
        file_frame.pack(fill="x", pady=(0, 10))
        
        self.file_label = ttk.Label(
            file_frame,
            text="No file selected",
            foreground="gray"
        )
        self.file_label.pack(side="left", fill="x", expand=True)
        
        ttk.Button(
            file_frame,
            text="📁 Browse...",
            command=self.browse_file
        ).pack(side="right", padx=(10, 0))
        
        # Action buttons
        button_frame = ttk.Frame(upload_frame)
        button_frame.pack(fill="x")
        
        self.validate_btn = ttk.Button(
            button_frame,
            text="🔍 Validate Data",
            command=self.validate_file,
            state="disabled"
        )
        self.validate_btn.pack(side="left", padx=(0, 10))
        
        self.upload_btn = ttk.Button(
            button_frame,
            text="⬆️ Upload to Database",
            command=self.upload_data,
            state="disabled"
        )
        self.upload_btn.pack(side="left")
        
        # Progress bar
        self.progress = ttk.Progressbar(upload_frame, mode='indeterminate')
        self.progress.pack(fill="x", pady=(10, 0))
    
    def create_preview_section(self, parent):
        """Create the data preview section"""
        
        preview_frame = ttk.LabelFrame(parent, text="2. Data Preview", padding=15)
        preview_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        # Scrollable text widget for preview
        preview_scroll = ttk.Scrollbar(preview_frame)
        preview_scroll.pack(side="right", fill="y")
        
        self.preview_text = tk.Text(
            preview_frame,
            height=10,
            wrap="none",
            yscrollcommand=preview_scroll.set,
            font=("Courier New", 9)
        )
        self.preview_text.pack(fill="both", expand=True)
        preview_scroll.config(command=self.preview_text.yview)
        
        self.preview_text.insert("1.0", "Preview will appear here after validation...\n")
        self.preview_text.config(state="disabled")
    
    def create_results_section(self, parent):
        """Create the results section"""
        
        results_frame = ttk.LabelFrame(parent, text="3. Upload Results", padding=15)
        results_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        # Scrollable text widget for results
        results_scroll = ttk.Scrollbar(results_frame)
        results_scroll.pack(side="right", fill="y")
        
        self.results_text = tk.Text(
            results_frame,
            height=8,
            wrap="word",
            yscrollcommand=results_scroll.set,
            font=("Segoe UI", 9)
        )
        self.results_text.pack(fill="both", expand=True)
        results_scroll.config(command=self.results_text.yview)
        
        self.results_text.insert("1.0", "Upload results will appear here...\n")
        self.results_text.config(state="disabled")
    
    def create_template_section(self, parent):
        """Create the template download section"""
        
        template_frame = ttk.LabelFrame(parent, text="📥 Download Templates", padding=15)
        template_frame.pack(fill="x")
        
        info_label = ttk.Label(
            template_frame,
            text="Download CSV templates to see the required format for uploads:",
            foreground="gray"
        )
        info_label.pack(anchor="w", pady=(0, 10))
        
        button_container = ttk.Frame(template_frame)
        button_container.pack(fill="x")
        
        ttk.Button(
            button_container,
            text="📄 Benchmark Rates Template",
            command=lambda: self.download_template('benchmark')
        ).pack(side="left", padx=(0, 10))
        
        ttk.Button(
            button_container,
            text="📄 Swap Rates Template",
            command=lambda: self.download_template('swap')
        ).pack(side="left", padx=(0, 10))
        
        ttk.Button(
            button_container,
            text="📄 OIS Rates Template",
            command=lambda: self.download_template('ois')
        ).pack(side="left")
    
    def browse_file(self):
        """Open file browser dialog"""
        filename = filedialog.askopenfilename(
            title="Select CSV File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if filename:
            self.selected_file = filename
            self.file_label.config(
                text=os.path.basename(filename),
                foreground="black"
            )
            self.validate_btn.config(state="normal")
            self.upload_btn.config(state="disabled")
            
            # Clear previous results
            self.clear_preview()
            self.clear_results()
    
    def validate_file(self):
        """Validate the selected file"""
        if not self.selected_file:
            messagebox.showerror("Error", "Please select a file first")
            return
        
        self.progress.start()
        self.validate_btn.config(state="disabled")
        
        try:
            rate_type = self.rate_type_var.get()
            
            # Parse based on type
            if rate_type == 'benchmark':
                records, errors = self.upload_handler.parse_benchmark_rates_csv(self.selected_file)
            elif rate_type == 'swap':
                records, errors = self.upload_handler.parse_swap_rates_csv(self.selected_file)
            elif rate_type == 'ois':
                records, errors = self.upload_handler.parse_ois_rates_csv(self.selected_file)
            else:
                raise ValueError(f"Invalid rate type: {rate_type}")
            
            # Display preview
            self.display_preview(records, errors)
            
            # Enable upload if no errors
            if records and not errors:
                self.upload_btn.config(state="normal")
                messagebox.showinfo(
                    "Validation Successful",
                    f"✅ File validated successfully!\n\n"
                    f"Found {len(records)} valid records.\n"
                    f"Click 'Upload to Database' to import."
                )
            elif errors:
                messagebox.showwarning(
                    "Validation Errors",
                    f"⚠️ Found {len(errors)} validation errors.\n\n"
                    f"Please check the preview and fix the errors."
                )
            else:
                messagebox.showerror(
                    "No Data",
                    "No valid records found in the file."
                )
        
        except Exception as e:
            messagebox.showerror("Error", f"Error validating file:\n{str(e)}")
        
        finally:
            self.progress.stop()
            self.validate_btn.config(state="normal")
    
    def upload_data(self):
        """Upload validated data to database"""
        if not self.selected_file:
            messagebox.showerror("Error", "Please select a file first")
            return
        
        # Confirm upload
        response = messagebox.askyesno(
            "Confirm Upload",
            "Are you sure you want to upload this data to the database?\n\n"
            "This action cannot be undone."
        )
        
        if not response:
            return
        
        self.progress.start()
        self.upload_btn.config(state="disabled")
        
        try:
            rate_type = self.rate_type_var.get()
            
            # Parse file again
            if rate_type == 'benchmark':
                records, errors = self.upload_handler.parse_benchmark_rates_csv(self.selected_file)
                success, duplicates, upload_errors = self.upload_handler.upload_benchmark_rates(records)
            elif rate_type == 'swap':
                records, errors = self.upload_handler.parse_swap_rates_csv(self.selected_file)
                success, duplicates, upload_errors = self.upload_handler.upload_swap_rates(records)
            elif rate_type == 'ois':
                records, errors = self.upload_handler.parse_ois_rates_csv(self.selected_file)
                success, duplicates, upload_errors = self.upload_handler.upload_ois_rates(records)
            
            # Display results
            self.display_results(success, duplicates, upload_errors)
            
            # Show summary
            if success > 0:
                messagebox.showinfo(
                    "Upload Complete",
                    f"✅ Upload completed successfully!\n\n"
                    f"New records added: {success}\n"
                    f"Duplicates skipped: {duplicates}\n"
                    f"Errors: {len(upload_errors)}"
                )
            else:
                messagebox.showwarning(
                    "Upload Failed",
                    f"⚠️ No records were uploaded.\n\n"
                    f"Duplicates: {duplicates}\n"
                    f"Errors: {len(upload_errors)}"
                )
        
        except Exception as e:
            messagebox.showerror("Error", f"Error uploading data:\n{str(e)}")
        
        finally:
            self.progress.stop()
            self.upload_btn.config(state="normal")
    
    def display_preview(self, records, errors):
        """Display data preview"""
        self.preview_text.config(state="normal")
        self.preview_text.delete("1.0", "end")
        
        if errors:
            self.preview_text.insert("end", "❌ VALIDATION ERRORS:\n\n", "error")
            for error in errors[:20]:  # Show first 20 errors
                self.preview_text.insert("end", f"  • {error}\n")
            if len(errors) > 20:
                self.preview_text.insert("end", f"\n  ... and {len(errors)-20} more errors\n")
            self.preview_text.insert("end", "\n" + "="*80 + "\n\n")
        
        if records:
            self.preview_text.insert("end", f"✅ VALID RECORDS ({len(records)}):\n\n", "success")
            self.preview_text.insert("end", f"{'Date':<12} {'Currency':<10} {'Type/Tenor':<15} {'Rate':<10}\n", "header")
            self.preview_text.insert("end", "-" * 50 + "\n")
            
            for i, record in enumerate(records[:50]):  # Show first 50
                rate_type = record.get('rate_type') or record.get('tenor', '')
                self.preview_text.insert(
                    "end",
                    f"{record['date']:<12} {record['currency']:<10} {rate_type:<15} {record['rate']:<10.4f}\n"
                )
            
            if len(records) > 50:
                self.preview_text.insert("end", f"\n... and {len(records)-50} more records\n")
        
        # Configure tags
        self.preview_text.tag_config("error", foreground="red", font=("Segoe UI", 9, "bold"))
        self.preview_text.tag_config("success", foreground="green", font=("Segoe UI", 9, "bold"))
        self.preview_text.tag_config("header", font=("Courier New", 9, "bold"))
        
        self.preview_text.config(state="disabled")
    
    def display_results(self, success, duplicates, errors):
        """Display upload results"""
        self.results_text.config(state="normal")
        self.results_text.delete("1.0", "end")
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        self.results_text.insert("end", f"📊 UPLOAD RESULTS - {timestamp}\n\n", "header")
        self.results_text.insert("end", f"✅ Successfully added: {success} records\n", "success")
        self.results_text.insert("end", f"⚠️ Duplicates skipped: {duplicates} records\n", "warning")
        self.results_text.insert("end", f"❌ Errors: {len(errors)}\n\n", "error")
        
        if errors:
            self.results_text.insert("end", "Error Details:\n", "header")
            for error in errors[:20]:
                self.results_text.insert("end", f"  • {error}\n")
            if len(errors) > 20:
                self.results_text.insert("end", f"\n  ... and {len(errors)-20} more errors\n")
        
        # Configure tags
        self.results_text.tag_config("header", font=("Segoe UI", 10, "bold"))
        self.results_text.tag_config("success", foreground="green")
        self.results_text.tag_config("warning", foreground="orange")
        self.results_text.tag_config("error", foreground="red")
        
        self.results_text.config(state="disabled")
    
    def clear_preview(self):
        """Clear preview text"""
        self.preview_text.config(state="normal")
        self.preview_text.delete("1.0", "end")
        self.preview_text.insert("1.0", "Preview will appear here after validation...\n")
        self.preview_text.config(state="disabled")
    
    def clear_results(self):
        """Clear results text"""
        self.results_text.config(state="normal")
        self.results_text.delete("1.0", "end")
        self.results_text.insert("1.0", "Upload results will appear here...\n")
        self.results_text.config(state="disabled")
    
    def download_template(self, rate_type):
        """Download CSV template"""
        filename = filedialog.asksaveasfilename(
            title=f"Save {rate_type.title()} Rates Template",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile=f"{rate_type}_rates_template.csv"
        )
        
        if filename:
            try:
                self.upload_handler.generate_template_csv(rate_type, filename)
                messagebox.showinfo(
                    "Template Downloaded",
                    f"Template saved successfully!\n\n{filename}\n\n"
                    f"Fill in your data and upload using this tool."
                )
            except Exception as e:
                messagebox.showerror("Error", f"Error saving template:\n{str(e)}")
