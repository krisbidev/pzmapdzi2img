"""
Main GUI window for Project Zomboid Map Stitcher
"""
import tkinter as tk
from tkinter import ttk
from . import styles


class MainWindow:
    """Main application window"""
    
    def __init__(self):
        """Initialize the main window"""
        self.root = tk.Tk()
        self.root.title(styles.WINDOW_TITLE)
        self.root.minsize(styles.WINDOW_MIN_WIDTH, styles.WINDOW_MIN_HEIGHT)
        
        # Center window on screen
        self._center_window()
        
        # Create UI elements
        self.create_menu()
        self.create_layout()
        self.create_status_bar()
        
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
        
        # Placeholder label
        ttk.Label(
            self.top_frame, 
            text="Path selection controls will go here"
        ).pack()
        
        # Middle section: Map selection and options
        self.middle_frame = ttk.LabelFrame(
            main_frame,
            text="Map Selection & Options",
            padding=styles.PAD_MEDIUM
        )
        self.middle_frame.pack(fill=tk.BOTH, expand=True, pady=(0, styles.PAD_MEDIUM))
        
        # Placeholder label
        ttk.Label(
            self.middle_frame,
            text="Map list and options will go here"
        ).pack()
        
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
    
    def run(self):
        """Start the GUI main loop"""
        self.root.mainloop()


def main():
    """Entry point for the GUI"""
    app = MainWindow()
    app.run()


if __name__ == "__main__":
    main()
