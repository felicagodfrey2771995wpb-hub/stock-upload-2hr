#!/usr/bin/env python3
"""
Graphical User Interface for Enhanced StockMate
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import queue
from pathlib import Path
from typing import Optional
import logging

from enhanced_stockmate import EnhancedStockMate

class StockMateGUI:
    """Graphical user interface for StockMate"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Enhanced StockMate - Stock Photo Upload Assistant")
        self.root.geometry("800x600")
        
        # Initialize StockMate
        self.stockmate = EnhancedStockMate()
        
        # Setup logging to GUI
        self.log_queue = queue.Queue()
        self.setup_logging()
        
        # Create GUI elements
        self.create_widgets()
        
        # Start log consumer
        self.consume_logs()
    
    def setup_logging(self):
        """Setup logging to GUI"""
        class QueueHandler(logging.Handler):
            def __init__(self, queue):
                super().__init__()
                self.queue = queue
            
            def emit(self, record):
                self.queue.put(self.format(record))
        
        # Add queue handler to logger
        logger = logging.getLogger()
        queue_handler = QueueHandler(self.log_queue)
        queue_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        logger.addHandler(queue_handler)
    
    def create_widgets(self):
        """Create GUI widgets"""
        # Create notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Main processing tab
        self.create_main_tab(notebook)
        
        # Settings tab
        self.create_settings_tab(notebook)
        
        # History tab
        self.create_history_tab(notebook)
        
        # Log tab
        self.create_log_tab(notebook)
    
    def create_main_tab(self, notebook):
        """Create main processing tab"""
        main_frame = ttk.Frame(notebook)
        notebook.add(main_frame, text="Process Images")
        
        # Input directory
        ttk.Label(main_frame, text="Input Directory:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.input_dir_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.input_dir_var, width=50).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(main_frame, text="Browse", command=self.browse_input_dir).grid(row=0, column=2, padx=5, pady=5)
        
        # Platform selection
        ttk.Label(main_frame, text="Platform:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.platform_var = tk.StringVar()
        platform_combo = ttk.Combobox(main_frame, textvariable=self.platform_var, state="readonly")
        platform_combo['values'] = self.stockmate.platform_manager.get_supported_platforms()
        platform_combo.grid(row=1, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        platform_combo.set("shutterstock")
        
        # Language selection
        ttk.Label(main_frame, text="Language:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.lang_var = tk.StringVar(value="en")
        lang_combo = ttk.Combobox(main_frame, textvariable=self.lang_var, state="readonly")
        lang_combo['values'] = ["en", "zh", "en,zh"]
        lang_combo.grid(row=2, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        
        # Max keywords
        ttk.Label(main_frame, text="Max Keywords:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.max_keywords_var = tk.IntVar(value=30)
        ttk.Spinbox(main_frame, from_=1, to=50, textvariable=self.max_keywords_var, width=10).grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Options frame
        options_frame = ttk.LabelFrame(main_frame, text="Options")
        options_frame.grid(row=4, column=0, columnspan=3, sticky=tk.W+tk.E, padx=5, pady=5)
        
        self.write_iptc_var = tk.BooleanVar()
        ttk.Checkbutton(options_frame, text="Write IPTC metadata", variable=self.write_iptc_var).grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        
        self.auto_upload_var = tk.BooleanVar()
        ttk.Checkbutton(options_frame, text="Auto-upload", variable=self.auto_upload_var).grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        self.mock_ai_var = tk.BooleanVar()
        ttk.Checkbutton(options_frame, text="Use Mock AI", variable=self.mock_ai_var).grid(row=0, column=2, sticky=tk.W, padx=5, pady=2)
        
        # Credentials frame (for auto-upload)
        self.credentials_frame = ttk.LabelFrame(main_frame, text="Credentials (for auto-upload)")
        self.credentials_frame.grid(row=5, column=0, columnspan=3, sticky=tk.W+tk.E, padx=5, pady=5)
        
        ttk.Label(self.credentials_frame, text="Username:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.username_var = tk.StringVar()
        ttk.Entry(self.credentials_frame, textvariable=self.username_var, width=30).grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(self.credentials_frame, text="Password:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.password_var = tk.StringVar()
        ttk.Entry(self.credentials_frame, textvariable=self.password_var, show="*", width=30).grid(row=1, column=1, padx=5, pady=2)
        
        # Output CSV
        ttk.Label(main_frame, text="Output CSV:").grid(row=6, column=0, sticky=tk.W, padx=5, pady=5)
        self.csv_path_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.csv_path_var, width=50).grid(row=6, column=1, padx=5, pady=5)
        ttk.Button(main_frame, text="Browse", command=self.browse_csv_path).grid(row=6, column=2, padx=5, pady=5)
        
        # Process button
        self.process_button = ttk.Button(main_frame, text="Process Images", command=self.process_images)
        self.process_button.grid(row=7, column=0, columnspan=3, pady=20)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=8, column=0, columnspan=3, sticky=tk.W+tk.E, padx=5, pady=5)
        
        # Configure grid weights
        main_frame.columnconfigure(1, weight=1)
    
    def create_settings_tab(self, notebook):
        """Create settings tab"""
        settings_frame = ttk.Frame(notebook)
        notebook.add(settings_frame, text="Settings")
        
        # Platform configurations
        platforms_frame = ttk.LabelFrame(settings_frame, text="Platform Configurations")
        platforms_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create treeview for platforms
        columns = ("Platform", "Max Keywords", "Max Title", "Max Description")
        self.platform_tree = ttk.Treeview(platforms_frame, columns=columns, show="headings")
        
        for col in columns:
            self.platform_tree.heading(col, text=col)
            self.platform_tree.column(col, width=150)
        
        self.platform_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Load platform data
        self.load_platform_data()
    
    def create_history_tab(self, notebook):
        """Create history tab"""
        history_frame = ttk.Frame(notebook)
        notebook.add(history_frame, text="Upload History")
        
        # Create treeview for history
        columns = ("Date", "Platform", "Image", "Status", "Message")
        self.history_tree = ttk.Treeview(history_frame, columns=columns, show="headings")
        
        for col in columns:
            self.history_tree.heading(col, text=col)
            self.history_tree.column(col, width=150)
        
        self.history_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Load history data
        self.load_history_data()
    
    def create_log_tab(self, notebook):
        """Create log tab"""
        log_frame = ttk.Frame(notebook)
        notebook.add(log_frame, text="Logs")
        
        # Create scrolled text widget for logs
        self.log_text = scrolledtext.ScrolledText(log_frame, height=20)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Clear log button
        ttk.Button(log_frame, text="Clear Logs", command=self.clear_logs).pack(pady=5)
    
    def browse_input_dir(self):
        """Browse for input directory"""
        directory = filedialog.askdirectory()
        if directory:
            self.input_dir_var.set(directory)
    
    def browse_csv_path(self):
        """Browse for CSV output path"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            self.csv_path_var.set(filename)
    
    def load_platform_data(self):
        """Load platform data into treeview"""
        for item in self.platform_tree.get_children():
            self.platform_tree.delete(item)
        
        for platform_name in self.stockmate.platform_manager.get_supported_platforms():
            config = self.stockmate.config.get_platform_config(platform_name)
            if config:
                self.platform_tree.insert("", tk.END, values=(
                    config.name,
                    config.max_keywords,
                    config.max_title_length,
                    config.max_description_length
                ))
    
    def load_history_data(self):
        """Load history data into treeview"""
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        
        for record in self.stockmate.upload_history[-50:]:  # Show last 50 records
            self.history_tree.insert("", tk.END, values=(
                record.get("timestamp", "")[:19],  # Truncate timestamp
                record.get("platform", ""),
                Path(record.get("image_path", "")).name,
                "Success" if record.get("success", False) else "Failed",
                record.get("message", "")[:50]  # Truncate message
            ))
    
    def clear_logs(self):
        """Clear log text widget"""
        self.log_text.delete(1.0, tk.END)
    
    def consume_logs(self):
        """Consume logs from queue and display in GUI"""
        try:
            while True:
                log_record = self.log_queue.get_nowait()
                self.log_text.insert(tk.END, log_record + "\n")
                self.log_text.see(tk.END)
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(100, self.consume_logs)
    
    def process_images(self):
        """Process images in a separate thread"""
        # Validate inputs
        if not self.input_dir_var.get():
            messagebox.showerror("Error", "Please select an input directory")
            return
        
        if not self.platform_var.get():
            messagebox.showerror("Error", "Please select a platform")
            return
        
        # Disable process button
        self.process_button.config(state="disabled")
        
        # Start processing in separate thread
        thread = threading.Thread(target=self._process_images_thread)
        thread.daemon = True
        thread.start()
    
    def _process_images_thread(self):
        """Process images in background thread"""
        try:
            # Get parameters
            input_dir = Path(self.input_dir_var.get())
            platform = self.platform_var.get()
            lang = self.lang_var.get()
            max_keywords = self.max_keywords_var.get()
            write_iptc = self.write_iptc_var.get()
            auto_upload = self.auto_upload_var.get()
            mock_ai = self.mock_ai_var.get()
            
            csv_path = Path(self.csv_path_var.get()) if self.csv_path_var.get() else None
            
            username = self.username_var.get() if auto_upload else None
            password = self.password_var.get() if auto_upload else None
            
            # Process images
            self.stockmate.process_images(
                input_dir=input_dir,
                platform=platform,
                lang=lang,
                max_keywords=max_keywords,
                write_iptc=write_iptc,
                csv_path=csv_path,
                auto_upload=auto_upload,
                username=username,
                password=password,
                mock_ai=mock_ai
            )
            
            # Show completion message
            self.root.after(0, lambda: messagebox.showinfo("Success", "Processing completed successfully"))
            
        except Exception as e:
            # Show error message
            self.root.after(0, lambda: messagebox.showerror("Error", f"Processing failed: {e}"))
        
        finally:
            # Re-enable process button
            self.root.after(0, lambda: self.process_button.config(state="normal"))

def main():
    """Main entry point for GUI"""
    root = tk.Tk()
    app = StockMateGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()