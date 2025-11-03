"""
Path Selector Widget

Widget for selecting map data directory and discovering available maps.
"""
import tkinter as tk
from tkinter import ttk, filedialog
from pathlib import Path
from typing import Optional, List, Dict, Any
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from map_image_generator.discovery import discover_maps
from map_image_generator.map_info import read_map_info
from . import styles


class PathSelector:
    """Widget for selecting and scanning map data directory"""
    
    def __init__(self, parent_frame, status_callback, maps_callback=None):
        """
        Initialize path selector widget
        
        Args:
            parent_frame: Parent tkinter frame
            status_callback: Function to call with status messages (message, type)
            maps_callback: Optional function to call when maps are discovered (maps_dict)
        """
        self.parent = parent_frame
        self.status_callback = status_callback
        self.maps_callback = maps_callback
        self.discovered_maps = {}
        
        # Create UI elements
        self._create_widgets()
    
    def _create_widgets(self):
        """Create all UI widgets"""
        # Path selection row
        path_frame = ttk.Frame(self.parent)
        path_frame.pack(fill=tk.X, pady=(0, styles.PAD_MEDIUM))
        
        ttk.Label(path_frame, text="Map Data Directory:").pack(side=tk.LEFT)
        
        self.path_var = tk.StringVar()
        self.path_entry = ttk.Entry(
            path_frame, 
            textvariable=self.path_var,
            width=50
        )
        self.path_entry.pack(side=tk.LEFT, padx=styles.PAD_MEDIUM, fill=tk.X, expand=True)
        
        # Bind Enter key and focus-out to trigger scan
        self.path_entry.bind('<Return>', lambda e: self.scan_for_maps())
        self.path_entry.bind('<FocusOut>', lambda e: self._check_and_scan())
        
        self.browse_btn = ttk.Button(
            path_frame,
            text="Browse...",
            command=self.browse_folder
        )
        self.browse_btn.pack(side=tk.LEFT)
    
    def _check_and_scan(self):
        """Check if path is valid and scan if it is"""
        path = self.path_var.get()
        if path and Path(path).exists() and Path(path).is_dir():
            self.scan_for_maps()
    
    def browse_folder(self):
        """Open folder picker dialog"""
        initial_dir = self.path_var.get()
        if not initial_dir or not Path(initial_dir).exists():
            initial_dir = str(Path.home())
        
        folder = filedialog.askdirectory(
            title="Select Map Data Directory",
            initialdir=initial_dir
        )
        
        if folder:
            self.path_var.set(folder)
            self.status_callback(f"Selected: {folder}", "info")
            # Auto-scan after selecting folder
            self.scan_for_maps()
    
    def scan_for_maps(self):
        """Scan selected directory for maps"""
        path = self.path_var.get()
        
        if not path:
            self.status_callback("Please select a directory first", "warning")
            return
        
        path_obj = Path(path)
        if not path_obj.exists():
            self.status_callback(f"Directory not found: {path}", "error")
            return
        
        if not path_obj.is_dir():
            self.status_callback(f"Not a directory: {path}", "error")
            return
        
        # Scan for maps
        try:
            self.status_callback("Scanning for maps...", "info")
            maps = self._discover_maps_simple(path_obj)
            
            if not maps:
                self.status_callback("No maps found in directory", "warning")
                return
            
            self.discovered_maps = maps
            self.status_callback(f"Found {len(maps)} map(s)", "success")
            
            # Notify callback if provided
            if self.maps_callback:
                self.maps_callback(maps)
            
        except Exception as e:
            self.status_callback(f"Error scanning: {str(e)}", "error")
    
    def _discover_maps_simple(self, base_path: Path) -> Dict[str, Dict[str, Any]]:
        """
        Simple map discovery - looks for map_info.json files
        
        Args:
            base_path: Path to map_data folder
            
        Returns:
            Dictionary of {map_name: {path, info, ...}}
        """
        maps = {}
        
        # Check for base_top
        base_top = base_path / 'base_top'
        if (base_top / 'map_info.json').exists():
            try:
                info = read_map_info(base_top)
                maps['base_top'] = {
                    'name': 'base_top',
                    'path': base_top,
                    'info': info
                }
            except Exception as e:
                self.status_callback(f"Warning: Could not read base_top: {e}", "warning")
        
        # Check for mod maps
        mod_maps_dir = base_path / 'mod_maps'
        if mod_maps_dir.exists() and mod_maps_dir.is_dir():
            for mod_folder in mod_maps_dir.iterdir():
                if not mod_folder.is_dir():
                    continue
                
                mod_base_top = mod_folder / 'base_top'
                if (mod_base_top / 'map_info.json').exists():
                    try:
                        info = read_map_info(mod_base_top)
                        map_name = mod_folder.name
                        maps[map_name] = {
                            'name': map_name,
                            'path': mod_base_top,
                            'info': info
                        }
                    except Exception as e:
                        self.status_callback(f"Warning: Could not read {mod_folder.name}: {e}", "warning")
        
        return maps
    
    def get_selected_path(self) -> Optional[Path]:
        """Get the currently selected path"""
        path = self.path_var.get()
        return Path(path) if path else None
    
    def get_discovered_maps(self) -> Dict[str, Dict[str, Any]]:
        """Get the discovered maps dictionary"""
        return self.discovered_maps
