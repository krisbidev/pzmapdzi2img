"""
Output configuration widget for map image generator.
Handles output path, format selection, and generation trigger.
"""
import tkinter as tk
from tkinter import ttk, filedialog
from pathlib import Path
from . import styles


class OutputConfig:
    """Widget for configuring output file and triggering generation"""
    
    def __init__(self, parent_frame, status_callback, on_generate_callback):
        """
        Initialize output configuration widget.
        
        Args:
            parent_frame: Parent tkinter frame
            status_callback: Function to call for status updates (message, type)
            on_generate_callback: Function to call when Generate is clicked
        """
        self.parent = parent_frame
        self.status_callback = status_callback
        self.on_generate_callback = on_generate_callback
        
        # State variables
        self.output_path_var = tk.StringVar()
        self.format_var = tk.StringVar(value="PNG")
        self.quality_var = tk.IntVar(value=85)
        
        # Widget references
        self.quality_frame = None
        self.generate_button = None
        
        # Default output path
        self._set_default_output_path()
        
        # Create widgets
        self._create_widgets()
    
    def _set_default_output_path(self):
        """Set default output path"""
        # Default to current directory / output.png
        default_path = Path.cwd() / "output.png"
        self.output_path_var.set(str(default_path))
    
    def _create_widgets(self):
        """Create all output configuration widgets"""
        # Output path section
        path_frame = ttk.Frame(self.parent)
        path_frame.pack(fill=tk.X, pady=(0, styles.PAD_SMALL))
        
        ttk.Label(
            path_frame,
            text="Output File:",
            width=12
        ).pack(side=tk.LEFT)
        
        self.path_entry = ttk.Entry(
            path_frame,
            textvariable=self.output_path_var,
            state=tk.DISABLED
        )
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=styles.PAD_SMALL)
        
        self.browse_button = ttk.Button(
            path_frame,
            text="Browse...",
            command=self._browse_output_path,
            state=tk.DISABLED
        )
        self.browse_button.pack(side=tk.LEFT)
        
        # Format section
        format_frame = ttk.Frame(self.parent)
        format_frame.pack(fill=tk.X, pady=styles.PAD_SMALL)
        
        ttk.Label(
            format_frame,
            text="Format:",
            width=12
        ).pack(side=tk.LEFT)
        
        # Radio buttons for format
        format_buttons_frame = ttk.Frame(format_frame)
        format_buttons_frame.pack(side=tk.LEFT, fill=tk.X)
        
        self.png_radio = ttk.Radiobutton(
            format_buttons_frame,
            text="PNG",
            variable=self.format_var,
            value="PNG",
            command=self._on_format_changed,
            state=tk.DISABLED
        )
        self.png_radio.pack(side=tk.LEFT, padx=(0, styles.PAD_MEDIUM))
        
        self.jpeg_radio = ttk.Radiobutton(
            format_buttons_frame,
            text="JPEG",
            variable=self.format_var,
            value="JPEG",
            command=self._on_format_changed,
            state=tk.DISABLED
        )
        self.jpeg_radio.pack(side=tk.LEFT, padx=(0, styles.PAD_MEDIUM))
        
        self.webp_radio = ttk.Radiobutton(
            format_buttons_frame,
            text="WebP",
            variable=self.format_var,
            value="WEBP",
            command=self._on_format_changed,
            state=tk.DISABLED
        )
        self.webp_radio.pack(side=tk.LEFT)
        
        # JPEG quality slider (initially hidden)
        self.quality_frame = ttk.Frame(self.parent)
        
        ttk.Label(
            self.quality_frame,
            text="JPEG Quality:",
            width=12
        ).pack(side=tk.LEFT)
        
        quality_control_frame = ttk.Frame(self.quality_frame)
        quality_control_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.quality_slider = ttk.Scale(
            quality_control_frame,
            from_=50,
            to=100,
            orient=tk.HORIZONTAL,
            variable=self.quality_var,
            command=self._on_quality_changed,
            state=tk.DISABLED
        )
        self.quality_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=styles.PAD_SMALL)
        
        self.quality_label = ttk.Label(
            quality_control_frame,
            text="85",
            width=4
        )
        self.quality_label.pack(side=tk.LEFT)
        
        # Generate button
        button_frame = ttk.Frame(self.parent)
        button_frame.pack(fill=tk.X, pady=(styles.PAD_MEDIUM, 0))
        
        self.generate_button = ttk.Button(
            button_frame,
            text="Generate Image",
            command=self._on_generate_clicked,
            state=tk.DISABLED
        )
        self.generate_button.pack(side=tk.RIGHT)
    
    def _browse_output_path(self):
        """Open file save dialog to choose output path"""
        # Get current path
        current_path = self.output_path_var.get()
        initial_dir = Path(current_path).parent if current_path else Path.cwd()
        initial_file = Path(current_path).name if current_path else ""
        
        # Set file type filters based on selected format
        format_map = {
            "PNG": ("PNG Image", "*.png"),
            "JPEG": ("JPEG Image", "*.jpg *.jpeg"),
            "WEBP": ("WebP Image", "*.webp")
        }
        
        selected_format = self.format_var.get()
        file_type = format_map.get(selected_format, ("All Files", "*.*"))
        
        # Show save dialog
        file_path = filedialog.asksaveasfilename(
            title="Save Output Image As",
            initialdir=initial_dir,
            initialfile=initial_file,
            defaultextension=self._get_extension(),
            filetypes=[file_type, ("All Files", "*.*")]
        )
        
        if file_path:
            self.output_path_var.set(file_path)
            # Update format based on extension if needed
            self._update_format_from_extension(file_path)
    
    def _get_extension(self):
        """Get file extension for current format"""
        ext_map = {
            "PNG": ".png",
            "JPEG": ".jpg",
            "WEBP": ".webp"
        }
        return ext_map.get(self.format_var.get(), ".png")
    
    def _update_format_from_extension(self, file_path):
        """Update format selection based on file extension"""
        ext = Path(file_path).suffix.lower()
        if ext in ['.png']:
            self.format_var.set("PNG")
        elif ext in ['.jpg', '.jpeg']:
            self.format_var.set("JPEG")
        elif ext in ['.webp']:
            self.format_var.set("WEBP")
        
        self._on_format_changed()
    
    def _on_format_changed(self):
        """Handle format selection change"""
        selected_format = self.format_var.get()
        
        # Show/hide quality slider for JPEG
        if selected_format == "JPEG":
            self.quality_frame.pack(fill=tk.X, pady=styles.PAD_SMALL, before=self.generate_button.master)
        else:
            self.quality_frame.pack_forget()
        
        # Update file extension in output path
        current_path = self.output_path_var.get()
        if current_path:
            path = Path(current_path)
            new_ext = self._get_extension()
            new_path = path.with_suffix(new_ext)
            self.output_path_var.set(str(new_path))
    
    def _on_quality_changed(self, value):
        """Handle quality slider change"""
        quality = int(float(value))
        self.quality_label.config(text=str(quality))
    
    def _on_generate_clicked(self):
        """Handle Generate button click"""
        # Validate output path
        output_path = self.get_output_path()
        if not output_path:
            self.status_callback("Please specify an output file path", "error")
            return
        
        # Check if parent directory exists or can be created
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self.status_callback(f"Cannot create output directory: {e}", "error")
            return
        
        # Call the callback
        self.on_generate_callback()
    
    def enable_controls(self, enabled=True):
        """
        Enable or disable all output controls.
        
        Args:
            enabled: True to enable, False to disable
        """
        state = tk.NORMAL if enabled else tk.DISABLED
        
        self.browse_button.config(state=state)
        self.png_radio.config(state=state)
        self.jpeg_radio.config(state=state)
        self.webp_radio.config(state=state)
        
        if self.format_var.get() == "JPEG":
            self.quality_slider.config(state=state)
        
        # Don't enable generate button here - use enable_generate() instead
    
    def enable_generate(self, enabled=True):
        """
        Enable or disable the Generate button specifically.
        
        Args:
            enabled: True to enable, False to disable
        """
        state = tk.NORMAL if enabled else tk.DISABLED
        self.generate_button.config(state=state)
    
    def get_output_path(self):
        """
        Get the output file path.
        
        Returns:
            Path object or None if not set
        """
        path_str = self.output_path_var.get()
        if path_str:
            return Path(path_str)
        return None
    
    def get_format(self):
        """
        Get the selected output format.
        
        Returns:
            Format string ('PNG', 'JPEG', or 'WEBP')
        """
        return self.format_var.get()
    
    def get_quality(self):
        """
        Get the JPEG quality setting.
        
        Returns:
            Quality value (50-100) if JPEG selected, else None
        """
        if self.format_var.get() == "JPEG":
            return self.quality_var.get()
        return None
    
    def update_default_filename(self, selected_layers, selected_level):
        """
        Update the default output filename based on selections.
        
        Args:
            selected_layers: List of selected layer indices
            selected_level: Selected zoom level
        """
        # Generate smart filename
        if len(selected_layers) == 1:
            layer_str = f"layer{selected_layers[0]}"
        elif len(selected_layers) == 8:
            layer_str = "all_layers"
        else:
            layer_str = f"{len(selected_layers)}_layers"
        
        filename = f"output_{layer_str}_level{selected_level}{self._get_extension()}"
        
        # Keep directory, update filename
        current_path = Path(self.output_path_var.get())
        new_path = current_path.parent / filename
        self.output_path_var.set(str(new_path))
