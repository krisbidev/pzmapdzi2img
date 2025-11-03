"""
Layer and Level Selector Widget

Widget for selecting layers (0-7) and zoom level with size estimation.
"""
import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Any, Optional
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from map_image_generator.dzi_parser import parse_dzi
from . import styles


class LayerLevelSelector:
    """Widget for selecting layers and zoom level"""
    
    def __init__(self, parent_frame, status_callback):
        """
        Initialize layer/level selector widget
        
        Args:
            parent_frame: Parent tkinter frame
            status_callback: Function to call with status messages (message, type)
        """
        self.parent = parent_frame
        self.status_callback = status_callback
        self.current_maps = []
        self.max_level = 15  # Default
        self.layer_vars = []  # List of BooleanVar for each layer checkbox
        
        # Create UI elements
        self._create_widgets()
    
    def _create_widgets(self):
        """Create all UI widgets"""
        # Layer selection - vertical layout
        layer_frame = ttk.LabelFrame(self.parent, text="Layers", padding=styles.PAD_MEDIUM)
        layer_frame.pack(fill=tk.BOTH, expand=True)
        
        # Select/Deselect All buttons
        button_frame = ttk.Frame(layer_frame)
        button_frame.pack(fill=tk.X, pady=(0, styles.PAD_SMALL))
        
        self.all_layers_btn = ttk.Button(button_frame, text="All", command=self._select_all_layers, width=8)
        self.all_layers_btn.pack(side=tk.LEFT, padx=(0, 2))
        
        self.none_layers_btn = ttk.Button(button_frame, text="None", command=self._deselect_all_layers, width=8)
        self.none_layers_btn.pack(side=tk.LEFT)
        
        # Create 8 checkboxes for layers 0-7 vertically
        self.layer_vars = []
        self.layer_checkboxes = []
        for i in range(8):
            var = tk.BooleanVar(value=True)  # Default: all layers enabled
            self.layer_vars.append(var)
            
            cb = ttk.Checkbutton(layer_frame, text=f"Layer {i}", variable=var,
                                command=self._update_size_estimate)
            cb.pack(anchor=tk.W, pady=2)
            self.layer_checkboxes.append(cb)
        
        # Initially disable all layer controls
        self._set_layer_controls_state(tk.DISABLED)
    
    def create_level_selector(self, parent_frame):
        """Create the level selector in a separate parent frame"""
        # Level selection
        level_frame = ttk.LabelFrame(parent_frame, text="Zoom Level", padding=styles.PAD_MEDIUM)
        level_frame.pack(fill=tk.X)
        
        ttk.Label(level_frame, text="Level:").pack(side=tk.LEFT, padx=(0, styles.PAD_SMALL))
        
        # Level slider
        self.level_var = tk.IntVar(value=12)
        self.level_scale = ttk.Scale(
            level_frame,
            from_=0,
            to=15,
            orient=tk.HORIZONTAL,
            variable=self.level_var,
            command=lambda v: self._on_level_changed(),
            state=tk.DISABLED  # Initially disabled
        )
        self.level_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, styles.PAD_SMALL))
        
        # Level label
        self.level_label = ttk.Label(level_frame, text="12", width=3)
        self.level_label.pack(side=tk.LEFT)
        
        # Size estimate below
        self.size_label = ttk.Label(
            parent_frame,
            text="Estimated output: Select maps and layers",
            foreground="gray",
            padding=(styles.PAD_MEDIUM, styles.PAD_SMALL)
        )
        self.size_label.pack(anchor=tk.W)
    
    def _on_level_changed(self):
        """Handle level slider change"""
        level = self.level_var.get()
        self.level_label.config(text=str(level))
        self._update_size_estimate()
    
    def update_maps_for_estimate(self, maps: List[Dict[str, Any]]):
        """
        Update the current maps for size estimation only (don't change max_level)
        
        Args:
            maps: List of map data dictionaries with 'path' and 'info' keys
        """
        self.current_maps = maps
        self._update_size_estimate()
    
    def set_maps(self, maps: List[Dict[str, Any]]):
        """
        Set the current maps and update available levels
        
        Args:
            maps: List of map data dictionaries with 'path' and 'info' keys
        """
        self.current_maps = maps
        
        if not maps:
            self.max_level = 15
            self.level_scale.config(to=15, state=tk.DISABLED)
            self.size_label.config(
                text="Estimated output: Select maps and layers",
                foreground="gray"
            )
            self._set_layer_controls_state(tk.DISABLED)
            return
        
        # Enable controls since we have maps
        self._set_layer_controls_state(tk.NORMAL)
        self.level_scale.config(state=tk.NORMAL)
        
        # Find highest max level among all maps
        max_levels = []
        for map_data in maps:
            dzi_file = map_data['path'] / 'layer0.dzi'
            if dzi_file.exists():
                try:
                    dzi_info = parse_dzi(dzi_file)
                    max_level = len(dzi_info['pyramid']) - 1
                    max_levels.append(max_level)
                except:
                    pass
        
        if max_levels:
            self.max_level = max(max_levels)
            self.level_scale.config(to=self.max_level)
            
            # Set default to reasonable level (max - 3 or 12, whichever is lower)
            default_level = min(self.max_level - 3, 12)
            default_level = max(default_level, 0)  # Don't go below 0
            self.level_var.set(default_level)
            self.level_label.config(text=str(default_level))
        
        self._update_size_estimate()
    
    def _update_size_estimate(self):
        """Calculate and display estimated output size"""
        if not self.current_maps:
            self.size_label.config(
                text="Estimated output: Select maps and layers",
                foreground="gray"
            )
            return
        
        try:
            # Get selected layers
            selected_layers = self.get_layers()
            if not selected_layers:
                self.size_label.config(
                    text="Estimated output: Select at least one layer",
                    foreground="orange"
                )
                return
            
            # Get selected level
            level = self.level_var.get()
            
            # Calculate global bounds from map_info data
            map_infos = [m['info'] for m in self.current_maps]
            
            # Simple bounds calculation
            min_x = min(-info['x0'] for info in map_infos)
            min_y = min(-info['y0'] for info in map_infos)
            max_x = max(-info['x0'] + info['w'] for info in map_infos)
            max_y = max(-info['y0'] + info['h'] for info in map_infos)
            
            # Calculate scale factor
            zoom_out = self.max_level - level
            scale_factor = 0.5 ** zoom_out
            
            # Calculate canvas size
            width = int((max_x - min_x) * scale_factor)
            height = int((max_y - min_y) * scale_factor)
            
            # Estimate file size (approximate)
            # PNG RGBA: 4 bytes per pixel, but compressed
            # Rough estimate: multiply by 0.5 for compression
            # Multiply by number of layers if multiple layers selected
            bytes_estimate = width * height * 4 * 0.5 * len(selected_layers)
            mb_estimate = bytes_estimate / (1024 * 1024)
            
            # Format size
            if mb_estimate < 1:
                size_str = f"{bytes_estimate / 1024:.0f} KB"
            else:
                size_str = f"{mb_estimate:.1f} MB"
            
            # Warning for large images
            color = "gray"
            if mb_estimate > 100:
                color = "red"
                warning = " ⚠ Very large!"
            elif mb_estimate > 50:
                color = "orange"
                warning = " ⚠ Large file"
            else:
                warning = ""
            
            # Add layer count to display
            layer_info = f" ({len(selected_layers)} layer{'s' if len(selected_layers) > 1 else ''})"
            
            self.size_label.config(
                text=f"Estimated output: {width:,} × {height:,} pixels (~{size_str}){layer_info}{warning}",
                foreground=color
            )
            
        except Exception as e:
            self.size_label.config(
                text=f"Error estimating size: {str(e)}",
                foreground="red"
            )
    
    def get_layers(self) -> List[int]:
        """Get list of selected layer numbers (0-7)"""
        return [i for i, var in enumerate(self.layer_vars) if var.get()]
    
    def get_level(self) -> int:
        """Get selected zoom level"""
        return self.level_var.get()
    
    def _select_all_layers(self):
        """Select all layer checkboxes"""
        for var in self.layer_vars:
            var.set(True)
        self._update_size_estimate()
        if self.status_callback:
            self.status_callback("All layers selected", "info")
    
    def _deselect_all_layers(self):
        """Deselect all layer checkboxes"""
        for var in self.layer_vars:
            var.set(False)
        self._update_size_estimate()
        if self.status_callback:
            self.status_callback("All layers deselected", "info")
    
    def _set_layer_controls_state(self, state):
        """Enable or disable all layer controls and level slider"""
        self.all_layers_btn.config(state=state)
        self.none_layers_btn.config(state=state)
        for cb in self.layer_checkboxes:
            cb.config(state=state)
        # Also disable the zoom level slider
        if hasattr(self, 'level_scale'):
            self.level_scale.config(state=state)
