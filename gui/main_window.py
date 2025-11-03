"""
Main GUI window for Project Zomboid Map Stitcher
"""
import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
import threading
from pathlib import Path
from . import styles
from .path_selector import PathSelector
from .map_selector import MapSelector
from .layer_level_selector import LayerLevelSelector
from .output_config import OutputConfig
from map_image_generator.stitcher import stitch_multi_map


class MainWindow:
    """Main application window"""
    
    def __init__(self):
        """Initialize the main window"""
        self.root = tk.Tk()
        self.root.title(styles.WINDOW_TITLE)
        self.root.minsize(styles.WINDOW_MIN_WIDTH, styles.WINDOW_MIN_HEIGHT)
        
        # Center window on screen
        self._center_window()
        
        # Initialize state
        self.all_maps = {}
        self.is_generating = False
        
        # Create UI elements (status bar first so path_selector can use it)
        self.create_menu()
        self.create_status_bar()
        self.create_layout()
        
        # Initial status message
        self.update_status("Ready", "info")
    
    def _center_window(self):
        """Center the window on screen"""
        self.root.update_idletasks()
        width = styles.WINDOW_MIN_WIDTH
        height = styles.WINDOW_MIN_HEIGHT + 50  # Add a bit more than minimum to avoid snap
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def create_menu(self):
        """Create the menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
    
    def create_layout(self):
        """Create the main layout sections"""
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding=styles.PAD_MEDIUM)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Top section: Input path configuration
        self.top_frame = ttk.LabelFrame(
            main_frame, 
            text="Input Configuration", 
            padding=styles.PAD_MEDIUM
        )
        self.top_frame.pack(fill=tk.X, pady=(0, styles.PAD_MEDIUM))
        
        # Add path selector widget
        self.path_selector = PathSelector(self.top_frame, self.update_status, self.on_maps_discovered)
        
        # Middle section: Map selection and options
        self.middle_frame = ttk.LabelFrame(
            main_frame,
            text="Map Selection & Options",
            padding=styles.PAD_MEDIUM
        )
        self.middle_frame.pack(fill=tk.BOTH, expand=True, pady=(0, styles.PAD_MEDIUM))
        
        # Create a horizontal split: maps on left, layers on right
        maps_layers_frame = ttk.Frame(self.middle_frame)
        maps_layers_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left side: Map selector
        maps_frame = ttk.Frame(maps_layers_frame)
        maps_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, styles.PAD_SMALL))
        self.map_selector = MapSelector(maps_frame, self.update_status, self.on_map_selection_changed)
        
        # Right side: Layer selector
        layers_frame = ttk.Frame(maps_layers_frame)
        layers_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(styles.PAD_SMALL, 0))
        self.layer_level_selector = LayerLevelSelector(layers_frame, self.update_status)
        
        # Separator
        ttk.Separator(self.middle_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=styles.PAD_MEDIUM)
        
        # Level selector below the map/layer split
        level_frame = ttk.Frame(self.middle_frame)
        level_frame.pack(fill=tk.X)
        self.layer_level_selector.create_level_selector(level_frame)
        
        # Separator
        ttk.Separator(self.middle_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=styles.PAD_MEDIUM)
        
        # Bottom section: Output configuration
        self.bottom_frame = ttk.Frame(main_frame, padding=styles.PAD_MEDIUM)
        self.bottom_frame.pack(fill=tk.X)
        
        # Output configuration widget
        self.output_config = OutputConfig(
            self.bottom_frame,
            status_callback=self.update_status,
            on_generate_callback=self.on_generate_image
        )
        
        # Initially disable output controls until maps are loaded
        self.output_config.enable_controls(False)
        self.output_config.enable_generate(False)
    
    def create_status_bar(self):
        """Create the status bar at the bottom"""
        self.status_frame = tk.Frame(self.root, relief=tk.SUNKEN, borderwidth=1)
        self.status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Canvas for progress background
        self.status_canvas = tk.Canvas(
            self.status_frame,
            height=25,
            highlightthickness=0
        )
        self.status_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Progress bar rectangle (initially hidden, full width)
        self.progress_rect = self.status_canvas.create_rectangle(
            0, 0, 0, 25,
            fill=styles.STATUS_INFO_BG,
            outline=""
        )
        
        # Status text on top of canvas
        self.status_text = self.status_canvas.create_text(
            5, 12,
            text="Ready",
            anchor=tk.W,
            font=("Segoe UI", 9)
        )
        
        # Store progress state
        self.progress_value = 0
        self.progress_max = 100
    
    def update_status(self, message, status_type='info'):
        """
        Update the status bar message
        
        Args:
            message: Status message to display
            status_type: Type of status ('info', 'warning', 'error', 'success')
        """
        # Update text
        self.status_canvas.itemconfig(self.status_text, text=message)
        
        # Update background color based on type (but only if not showing progress)
        if self.progress_value == 0:
            bg_colors = {
                'info': styles.STATUS_INFO_BG,
                'warning': styles.STATUS_WARNING_BG,
                'error': styles.STATUS_ERROR_BG,
                'success': styles.STATUS_SUCCESS_BG
            }
            bg_color = bg_colors.get(status_type, styles.STATUS_INFO_BG)
            self.status_canvas.config(background=bg_color)
            self.status_canvas.itemconfig(self.progress_rect, width=0)
        
        # Force update
        self.root.update_idletasks()
        
        # Force update
        self.root.update_idletasks()
    
    def update_progress(self, current, total, message):
        """
        Update status bar with progress animation
        
        Args:
            current: Current step
            total: Total steps
            message: Status message
        """
        self.progress_value = current
        self.progress_max = total
        
        # Calculate percentage and width
        if total > 0:
            percentage = current / total
            canvas_width = self.status_canvas.winfo_width()
            progress_width = int(canvas_width * percentage)
        else:
            progress_width = 0
        
        # Update progress bar rectangle
        self.status_canvas.coords(self.progress_rect, 0, 0, progress_width, 25)
        self.status_canvas.itemconfig(self.progress_rect, fill="#b3d9ff")  # Light blue
        self.status_canvas.config(background="white")
        
        # Update text
        self.status_canvas.itemconfig(self.status_text, text=message)
        
        # Force update
        self.root.update_idletasks()
    
    def clear_progress(self):
        """Clear progress bar and return to normal status display"""
        self.progress_value = 0
        self.progress_max = 100
        self.status_canvas.coords(self.progress_rect, 0, 0, 0, 25)
        self.status_canvas.config(background=styles.STATUS_INFO_BG)
        self.root.update_idletasks()
    
    def on_maps_discovered(self, maps):
        """Callback when maps are discovered by path selector"""
        self.map_selector.populate_maps(maps)
        
        # Store all maps for later filtering
        self.all_maps = maps
        
        # Update layer/level selector with all maps initially
        maps_list = [{'path': data['path'], 'info': data['info']} 
                     for data in maps.values()]
        self.layer_level_selector.set_maps(maps_list)
        
        # Enable output controls when maps are available
        self.output_config.enable_controls(True)
        self._check_generate_button_state()
    
    def on_map_selection_changed(self):
        """Callback when map selection changes (checkbox toggled)"""
        print(f"DEBUG: on_map_selection_changed called, all_maps has {len(self.all_maps)} items")
        
        # Get only the selected maps
        selected_map_paths = self.map_selector.get_selected_maps()
        print(f"DEBUG: Selected {len(selected_map_paths)} maps")
        
        # Convert to the format expected by layer_level_selector
        selected_maps_list = []
        for map_name, map_data in self.all_maps.items():
            if map_data['path'] in selected_map_paths:
                selected_maps_list.append({
                    'path': map_data['path'],
                    'info': map_data['info']
                })
        
        print(f"DEBUG: Updating estimate with {len(selected_maps_list)} maps")
        # Update size estimate with only selected maps
        self.layer_level_selector.update_maps_for_estimate(selected_maps_list)
        
        # Check if Generate button should be enabled
        self._check_generate_button_state()
    
    def _check_generate_button_state(self):
        """Enable Generate button only if valid configuration exists"""
        # Check if we have maps selected
        selected_maps = self.map_selector.get_selected_maps()
        
        # Check if we have layers selected
        selected_layers = self.layer_level_selector.get_layers()
        
        # Check if output path is set
        output_path = self.output_config.get_output_path()
        
        # Enable only if all conditions met
        can_generate = (
            len(selected_maps) > 0 and
            len(selected_layers) > 0 and
            output_path is not None and
            not self.is_generating
        )
        
        self.output_config.enable_generate(can_generate)
    
    def on_generate_image(self):
        """Handle Generate Image button click"""
        # Collect all parameters
        selected_map_paths = self.map_selector.get_selected_maps()
        selected_layers = self.layer_level_selector.get_layers()
        selected_level = self.layer_level_selector.get_level()
        output_path = self.output_config.get_output_path()
        output_format = self.output_config.get_format()
        jpeg_quality = self.output_config.get_quality()
        
        # Validation (should already be done, but double-check)
        if not selected_map_paths:
            self.update_status("Please select at least one map", "error")
            return
        
        if not selected_layers:
            self.update_status("Please select at least one layer", "error")
            return
        
        if not output_path:
            self.update_status("Please specify an output path", "error")
            return
        
        # Confirm if file exists
        if output_path.exists():
            response = messagebox.askyesno(
                "Overwrite File?",
                f"File already exists:\n{output_path}\n\nOverwrite it?",
                parent=self.root
            )
            if not response:
                return
        
        # Disable controls during generation
        self.is_generating = True
        self._set_all_controls_state(False)
        
        # Start generation in background thread
        thread = threading.Thread(
            target=self._generate_image_thread,
            args=(selected_map_paths, selected_layers, selected_level, 
                  output_path, output_format, jpeg_quality)
        )
        thread.daemon = True
        thread.start()
    
    def _generate_image_thread(self, map_paths, layers, level, output_path, 
                              output_format, jpeg_quality):
        """
        Run image generation in background thread.
        
        This prevents the GUI from freezing during long operations.
        Generates a single image with all selected layers combined.
        """
        try:
            from PIL import Image
            from map_image_generator.bounds import calculate_global_bounds
            from map_image_generator.stitcher import _calculate_map_levels, _stitch_map_onto_canvas, _save_image
            from map_image_generator.tile_loader import load_tiles_for_level
            
            # Weight the steps: save typically takes 80-90% of total time
            # Give save operation a weight of 50 "virtual steps" to reflect this
            stitch_steps = len(layers) * len(map_paths)
            save_weight = 50  # Make save step count as 50 steps
            total_steps = 2 + stitch_steps + save_weight
            current_step = 0
            
            # Step 1: Calculate bounds
            current_step += 1
            self.root.after(0, self.update_progress, current_step, total_steps, 
                          "Calculating global bounds...")
            
            bounds = calculate_global_bounds(map_paths, layers[0])
            
            # Step 2: Calculate zoom levels
            current_step += 1
            self.root.after(0, self.update_progress, current_step, total_steps,
                          "Calculating zoom levels...")
            
            map_levels = _calculate_map_levels(map_paths, layers[0], level)
            scale_factor = map_levels['scale_factor']
            canvas_width = int(bounds['width'] * scale_factor)
            canvas_height = int(bounds['height'] * scale_factor)
            
            # Create combined canvas
            self.root.after(0, self.update_progress, current_step, total_steps,
                          f"Creating canvas ({canvas_width}×{canvas_height})...")
            
            combined_image = Image.new('RGBA', (canvas_width, canvas_height), (0, 0, 0, 0))
            
            # Stitch each layer onto the same canvas
            for layer_idx, layer in enumerate(layers, 1):
                for map_idx, map_path in enumerate(map_paths, 1):
                    current_step += 1
                    
                    # Update progress
                    msg = f"Layer {layer}/{len(layers)}, Map {map_idx}/{len(map_paths)}: {map_path.name}"
                    self.root.after(0, self.update_progress, current_step, total_steps, msg)
                    
                    # Stitch this map for this layer
                    _stitch_map_onto_canvas(
                        output_image=combined_image,
                        map_path=map_path,
                        layer=layer,
                        map_levels=map_levels,
                        bounds=bounds,
                        scale_factor=scale_factor
                    )
            
            # Prepare for save
            save_format = output_format.upper()
            if save_format == 'JPG':
                save_format = 'JPEG'
            
            # Convert if needed for JPEG
            save_image = combined_image
            if save_format == 'JPEG' and combined_image.mode == 'RGBA':
                current_step += 1
                self.root.after(0, self.update_progress, current_step, total_steps,
                              "Converting to JPEG format...")
                background = Image.new('RGB', combined_image.size, (255, 255, 255))
                background.paste(combined_image, mask=combined_image.split()[3])
                save_image = background
            
            # Create directory
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save (this is the slow part - show as starting point)
            current_step += 1
            self.root.after(0, self.update_progress, current_step, total_steps,
                          f"Saving {output_format} file (this may take a while)...")
            
            # Prepare save kwargs
            save_kwargs = {}
            if save_format == 'JPEG':
                save_kwargs = {'quality': jpeg_quality or 95, 'optimize': True}
            elif save_format == 'WEBP':
                save_kwargs = {'quality': 95, 'method': 6}
            elif save_format == 'PNG':
                save_kwargs = {'optimize': True}
            
            # Actual save (blocking operation that takes most of the time)
            save_image.save(output_path, format=save_format, **save_kwargs)
            
            # Complete (jump to 100%)
            current_step = total_steps
            self.root.after(0, self.update_progress, current_step, total_steps,
                          "Save complete!")
            
            # Success!
            file_size = output_path.stat().st_size / (1024 * 1024)
            message = f"Saved {output_path.name} ({file_size:.1f} MB)"
            self.root.after(0, self._generation_complete, True, message)
            
        except Exception as e:
            # Error occurred
            error_msg = f"Generation failed: {str(e)}"
            self.root.after(0, self._generation_complete, False, error_msg)
    
    def _generation_complete(self, success, message):
        """
        Called when generation completes (success or failure).
        
        Args:
            success: True if generation succeeded
            message: Status message to display
        """
        # Clear progress bar
        self.clear_progress()
        
        # Re-enable controls
        self.is_generating = False
        self._set_all_controls_state(True)
        
        # Update status
        status_type = "success" if success else "error"
        self.update_status(message, status_type)
        
        # Show message box for important notifications
        if success:
            messagebox.showinfo("Success", message, parent=self.root)
        else:
            messagebox.showerror("Error", message, parent=self.root)
    
    def _generation_cancelled(self):
        """Called when generation is cancelled by user"""
        # Clear progress bar
        self.clear_progress()
        
        # Re-enable controls
        self.is_generating = False
        self._set_all_controls_state(True)
        
        # Update status
        self.update_status("Generation cancelled by user", "warning")
    
    def _set_all_controls_state(self, enabled):
        """
        Enable or disable all controls (during generation).
        
        Args:
            enabled: True to enable, False to disable
        """
        # Path selector
        self.path_selector.set_buttons_state(enabled)
        
        # Map selector
        self.map_selector._set_buttons_state(tk.NORMAL if enabled else tk.DISABLED)
        
        # Layer/level selector
        self.layer_level_selector._set_layer_controls_state(
            tk.NORMAL if enabled else tk.DISABLED
        )
        
        # Output config
        self.output_config.enable_controls(enabled)
        
        # Generate button specifically
        if enabled:
            self._check_generate_button_state()
        else:
            self.output_config.enable_generate(False)
    
    def show_about(self):
        """Show About dialog"""
        # Create custom dialog window
        about_win = tk.Toplevel(self.root)
        about_win.title("About pzmapdzi2img")
        about_win.resizable(False, False)
        about_win.transient(self.root)
        about_win.grab_set()
        
        # Center on parent window
        about_win.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 150
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 100
        about_win.geometry(f"+{x}+{y}")
        
        # Content frame
        content = ttk.Frame(about_win, padding=20)
        content.pack()
        
        # About text
        ttk.Label(
            content,
            text="pzmapdzi2img - Map Image Generator\n\n"
                 "Converts pzmap2dzi DZI tiles into single images.\n\n"
                 "Created by Kris"
        ).pack()
        
        # Clickable Ko-fi link
        kofi_label = ttk.Label(
            content,
            text="Support: ko-fi.com/krispz",
            foreground="blue",
            cursor="hand2"
        )
        kofi_label.pack()
        kofi_label.bind("<Button-1>", lambda e: webbrowser.open("https://ko-fi.com/krispz"))
        
        # Close button
        ttk.Button(
            content,
            text="Close",
            command=about_win.destroy
        ).pack(pady=(20, 0))
    
    def run(self):
        """Start the GUI main loop"""
        self.root.mainloop()


def main():
    """Entry point for the GUI"""
    app = MainWindow()
    app.run()


if __name__ == "__main__":
    main()
