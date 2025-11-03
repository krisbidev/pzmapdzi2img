"""
Main GUI window for Project Zomboid Map Stitcher
"""
import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
from . import styles
from .path_selector import PathSelector
from .map_selector import MapSelector


class MainWindow:
    """Main application window"""
    
    def __init__(self):
        """Initialize the main window"""
        self.root = tk.Tk()
        self.root.title(styles.WINDOW_TITLE)
        self.root.minsize(styles.WINDOW_MIN_WIDTH, styles.WINDOW_MIN_HEIGHT)
        
        # Center window on screen
        self._center_window()
        
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
        height = styles.WINDOW_MIN_HEIGHT
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
        
        # Add map selector widget
        self.map_selector = MapSelector(self.middle_frame, self.update_status)
        
        # Bottom section: Action buttons
        self.bottom_frame = ttk.Frame(main_frame, padding=styles.PAD_MEDIUM)
        self.bottom_frame.pack(fill=tk.X)
        
        # Placeholder button
        ttk.Button(
            self.bottom_frame,
            text="Generate Image",
            state=tk.DISABLED
        ).pack(side=tk.RIGHT)
    
    def create_status_bar(self):
        """Create the status bar at the bottom"""
        self.status_frame = ttk.Frame(self.root, relief=tk.SUNKEN, borderwidth=1)
        self.status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_label = ttk.Label(
            self.status_frame,
            text="Ready",
            anchor=tk.W,
            padding=(styles.PAD_SMALL, 2)
        )
        self.status_label.pack(fill=tk.X)
    
    def update_status(self, message, status_type='info'):
        """
        Update the status bar message
        
        Args:
            message: Status message to display
            status_type: Type of status ('info', 'warning', 'error', 'success')
        """
        self.status_label.config(text=message)
        
        # Update background color based on type
        bg_colors = {
            'info': styles.STATUS_INFO_BG,
            'warning': styles.STATUS_WARNING_BG,
            'error': styles.STATUS_ERROR_BG,
            'success': styles.STATUS_SUCCESS_BG
        }
        bg_color = bg_colors.get(status_type, styles.STATUS_INFO_BG)
        self.status_label.config(background=bg_color)
        
        # Force update
        self.root.update_idletasks()
    
    def on_maps_discovered(self, maps):
        """Callback when maps are discovered by path selector"""
        self.map_selector.populate_maps(maps)
    
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
