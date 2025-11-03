"""
Map Selector Widget

Widget for selecting which maps to include and controlling their stacking order.
"""
import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Any, Optional
from . import styles


class MapSelector:
    """Widget for selecting and ordering maps"""
    
    def __init__(self, parent_frame, status_callback, selection_changed_callback=None):
        """
        Initialize map selector widget
        
        Args:
            parent_frame: Parent tkinter frame
            status_callback: Function to call with status messages (message, type)
            selection_changed_callback: Function to call when map selection changes
        """
        self.parent = parent_frame
        self.status_callback = status_callback
        self.selection_changed_callback = selection_changed_callback
        self.map_items = []  # List of {name, path, info, enabled, var}
        
        # Create UI elements
        self._create_widgets()
    
    def _create_widgets(self):
        """Create all UI widgets"""
        # Instructions
        ttk.Label(
            self.parent,
            text="Select maps to include (first = bottom layer):"
        ).pack(anchor=tk.W, pady=(0, styles.PAD_SMALL))
        
        # Container for list and buttons
        container = ttk.Frame(self.parent)
        container.pack(fill=tk.BOTH, expand=True)
        
        # Scrollable map list
        list_frame = ttk.Frame(container)
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Canvas + scrollbar for custom scrollable frame
        canvas = tk.Canvas(list_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=canvas.yview)
        self.map_list_frame = ttk.Frame(canvas)
        
        self.map_list_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.map_list_frame, anchor=tk.NW)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Bind mousewheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Control buttons (right side)
        button_frame = ttk.Frame(container)
        button_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(styles.PAD_MEDIUM, 0))
        
        # Up button
        self.up_btn = ttk.Button(
            button_frame,
            text="↑ Up",
            command=self.move_up,
            width=8
        )
        self.up_btn.pack(pady=(0, styles.PAD_SMALL))
        
        # Down button
        self.down_btn = ttk.Button(
            button_frame,
            text="↓ Down",
            command=self.move_down,
            width=8
        )
        self.down_btn.pack(pady=(0, styles.PAD_MEDIUM))
        
        # Select All button
        self.all_btn = ttk.Button(
            button_frame,
            text="All",
            command=self._select_all_maps,
            width=8
        )
        self.all_btn.pack(pady=(0, styles.PAD_SMALL))
        
        # Deselect All button
        self.none_btn = ttk.Button(
            button_frame,
            text="None",
            command=self._deselect_all_maps,
            width=8
        )
        self.none_btn.pack()
        
        # Initially disable all buttons
        self._set_buttons_state(tk.DISABLED)
        
        # Initially disable buttons
        self.up_btn.config(state=tk.DISABLED)
        self.down_btn.config(state=tk.DISABLED)
        
        # Placeholder message
        ttk.Label(
            self.map_list_frame,
            text="No maps loaded. Use Browse to select a folder.",
            foreground="gray"
        ).pack(pady=20)
    
    def populate_maps(self, maps: Dict[str, Dict[str, Any]]):
        """
        Populate the map list from discovered maps
        
        Args:
            maps: Dictionary of {map_name: {name, path, info}}
        """
        # Clear existing items
        for widget in self.map_list_frame.winfo_children():
            widget.destroy()
        self.map_items.clear()
        
        if not maps:
            ttk.Label(
                self.map_list_frame,
                text="No maps found.",
                foreground="gray"
            ).pack(pady=20)
            self._set_buttons_state(tk.DISABLED)
            return
        
        # Enable buttons since we have maps
        self._set_buttons_state(tk.NORMAL)
        self.up_btn.config(state=tk.DISABLED)  # Initially disabled until selection
        self.down_btn.config(state=tk.DISABLED)
        
        # Sort maps: base_top first, then others
        sorted_maps = []
        if 'base_top' in maps:
            sorted_maps.append(('base_top', maps['base_top']))
        for name, data in maps.items():
            if name != 'base_top':
                sorted_maps.append((name, data))
        
        # Create map items
        for idx, (name, data) in enumerate(sorted_maps):
            self._create_map_item(idx, name, data)
        
        self.status_callback(f"Loaded {len(self.map_items)} map(s)", "info")
    
    def _create_map_item(self, idx: int, name: str, data: Dict[str, Any]):
        """Create a single map item row"""
        item_frame = ttk.Frame(self.map_list_frame)
        item_frame.pack(fill=tk.X, pady=2)
        
        # Checkbox variable
        var = tk.BooleanVar(value=True)
        
        # Checkbox
        cb = ttk.Checkbutton(
            item_frame,
            variable=var,
            command=self._on_selection_changed
        )
        cb.pack(side=tk.LEFT)
        
        # Map info label
        info = data['info']
        w = info['w']
        h = info['h']
        label_text = f"{name} ({w}×{h})"
        
        label = ttk.Label(item_frame, text=label_text)
        label.pack(side=tk.LEFT, padx=(5, 5), fill=tk.X, expand=True)
        
        # Selection highlight (bind click to select entire row)
        def select_item(event=None):
            self._select_item(idx)
        
        label.bind("<Button-1>", select_item)
        item_frame.bind("<Button-1>", select_item)
        cb.bind("<Button-1>", lambda e: self._select_item(idx), add="+")
        
        # Store item data
        self.map_items.append({
            'name': name,
            'path': data['path'],
            'info': info,
            'enabled': True,
            'var': var,
            'frame': item_frame,
            'label': label,
            'checkbox': cb
        })
    
    def _select_item(self, idx: int):
        """Select a map item (for move up/down operations)"""
        # Deselect all
        for item in self.map_items:
            item['label'].config(foreground='black')
        
        # Select clicked item
        if 0 <= idx < len(self.map_items):
            self.map_items[idx]['label'].config(foreground='blue')
            self.selected_idx = idx
            
            # Enable/disable buttons based on position
            self.up_btn.config(state=tk.NORMAL if idx > 0 else tk.DISABLED)
            self.down_btn.config(state=tk.NORMAL if idx < len(self.map_items) - 1 else tk.DISABLED)
    
    def _on_selection_changed(self):
        """Handle checkbox state change"""
        print("DEBUG: _on_selection_changed called")
        # Update enabled state
        for item in self.map_items:
            item['enabled'] = item['var'].get()
        
        enabled_count = sum(1 for item in self.map_items if item['enabled'])
        self.status_callback(f"{enabled_count} of {len(self.map_items)} map(s) selected", "info")
        
        # Notify parent that selection changed (for size estimate update)
        print(f"DEBUG: callback is {self.selection_changed_callback}")
        if self.selection_changed_callback:
            print("DEBUG: Calling selection_changed_callback")
            self.selection_changed_callback()
        else:
            print("DEBUG: No callback set")
    
    def move_up(self):
        """Move selected map up in the list"""
        if not hasattr(self, 'selected_idx'):
            return
        
        idx = self.selected_idx
        if idx <= 0:
            return
        
        # Swap items in list
        self.map_items[idx], self.map_items[idx - 1] = \
            self.map_items[idx - 1], self.map_items[idx]
        
        # Rebuild UI
        self._rebuild_ui()
        
        # Update selection
        self._select_item(idx - 1)
    
    def move_down(self):
        """Move selected map down in the list"""
        if not hasattr(self, 'selected_idx'):
            return
        
        idx = self.selected_idx
        if idx >= len(self.map_items) - 1:
            return
        
        # Swap items in list
        self.map_items[idx], self.map_items[idx + 1] = \
            self.map_items[idx + 1], self.map_items[idx]
        
        # Rebuild UI
        self._rebuild_ui()
        
        # Update selection
        self._select_item(idx + 1)
    
    def _rebuild_ui(self):
        """Rebuild the UI after reordering"""
        # Clear frames
        for widget in self.map_list_frame.winfo_children():
            widget.destroy()
        
        # Recreate items in new order
        for idx, item in enumerate(self.map_items):
            item_frame = ttk.Frame(self.map_list_frame)
            item_frame.pack(fill=tk.X, pady=2)
            
            # Checkbox
            cb = ttk.Checkbutton(
                item_frame,
                variable=item['var'],
                command=self._on_selection_changed
            )
            cb.pack(side=tk.LEFT)
            
            # Label
            info = item['info']
            w = info['w']
            h = info['h']
            label_text = f"{item['name']} ({w}×{h})"
            
            label = ttk.Label(item_frame, text=label_text)
            label.pack(side=tk.LEFT, padx=(5, 0))
            
            # Bind click
            def select_item(i=idx):
                return lambda e: self._select_item(i)
            
            label.bind("<Button-1>", select_item())
            item_frame.bind("<Button-1>", select_item())
            
            # Update stored references
            item['frame'] = item_frame
            item['label'] = label
    
    def get_selected_maps(self) -> List[Any]:
        """
        Get list of selected map paths in current order
        
        Returns:
            List of Path objects for enabled maps
        """
        return [item['path'] for item in self.map_items if item['enabled']]
    
    def get_map_order(self) -> Optional[List[int]]:
        """
        Get the map order indices for stitch_multi_map
        
        Returns:
            None if using default order, or list of indices if reordered
        """
        # Check if order has been changed from default
        # (For now, we'll always return None and let auto-ordering handle it)
        # TODO: Could implement custom ordering if needed
        return None
    
    def _select_all_maps(self):
        """Select all map checkboxes"""
        for item in self.map_items:
            item['var'].set(True)
            item['enabled'] = True
        self._on_selection_changed()
    
    def _deselect_all_maps(self):
        """Deselect all map checkboxes"""
        for item in self.map_items:
            item['var'].set(False)
            item['enabled'] = False
        self._on_selection_changed()
    
    def _set_buttons_state(self, state):
        """Enable or disable all control buttons and checkboxes"""
        self.up_btn.config(state=state)
        self.down_btn.config(state=state)
        self.all_btn.config(state=state)
        self.none_btn.config(state=state)
        
        # Also disable/enable all map checkboxes
        for item in self.map_items:
            item['checkbox'].config(state=state)
