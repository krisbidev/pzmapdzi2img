"""
Progress Tracker Widget

Displays progress bar and status during image generation operations.
"""
import tkinter as tk
from tkinter import ttk
import time
from . import styles


class ProgressTracker:
    """Widget for displaying progress during long operations"""
    
    def __init__(self, parent_frame):
        """
        Initialize progress tracker widget.
        
        Args:
            parent_frame: Parent tkinter frame
        """
        self.parent = parent_frame
        self.start_time = None
        self.cancel_requested = False
        
        # Widget references
        self.progress_frame = None
        self.progress_bar = None
        self.status_label = None
        self.cancel_button = None
        
        # Create widgets (initially hidden)
        self._create_widgets()
    
    def _create_widgets(self):
        """Create all progress UI widgets"""
        # Progress frame (initially not packed)
        self.progress_frame = ttk.Frame(self.parent)
        
        # Status label
        self.status_label = ttk.Label(
            self.progress_frame,
            text="",
            anchor=tk.W
        )
        self.status_label.pack(fill=tk.X, pady=(0, styles.PAD_SMALL))
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            mode='determinate',
            length=400
        )
        self.progress_bar.pack(fill=tk.X, pady=(0, styles.PAD_SMALL))
        
        # Button frame for cancel button
        button_frame = ttk.Frame(self.progress_frame)
        button_frame.pack(fill=tk.X)
        
        self.cancel_button = ttk.Button(
            button_frame,
            text="Cancel",
            command=self._on_cancel_clicked
        )
        self.cancel_button.pack(side=tk.RIGHT)
    
    def start(self, message="Starting..."):
        """
        Start progress tracking - show UI and reset state.
        
        Args:
            message: Initial status message
        """
        self.cancel_requested = False
        self.start_time = time.time()
        
        # Reset progress bar
        self.progress_bar['value'] = 0
        self.progress_bar['maximum'] = 100
        
        # Update status
        self.status_label.config(text=message)
        
        # Show progress UI
        self.progress_frame.pack(fill=tk.X, pady=styles.PAD_MEDIUM)
        
        # Force update
        self.parent.update_idletasks()
    
    def update(self, current, total, message):
        """
        Update progress display.
        
        Args:
            current: Current step number (0-based or 1-based)
            total: Total number of steps
            message: Status message to display
            
        Returns:
            True if should continue, False if cancelled
        """
        if self.cancel_requested:
            return False
        
        # Calculate percentage
        if total > 0:
            percentage = int((current / total) * 100)
            self.progress_bar['value'] = percentage
        
        # Update status message
        elapsed = time.time() - self.start_time
        elapsed_str = self._format_time(elapsed)
        
        full_message = f"{message} ({elapsed_str})"
        self.status_label.config(text=full_message)
        
        # Force update
        self.parent.update_idletasks()
        
        return True
    
    def complete(self, message, success=True):
        """
        Mark operation as complete.
        
        Args:
            message: Completion message
            success: True if successful, False if error
        """
        # Set progress to 100%
        self.progress_bar['value'] = 100
        
        # Show final message with elapsed time
        elapsed = time.time() - self.start_time
        elapsed_str = self._format_time(elapsed)
        
        full_message = f"{message} ({elapsed_str})"
        self.status_label.config(text=full_message)
        
        # Disable cancel button
        self.cancel_button.config(state=tk.DISABLED)
        
        # Force update
        self.parent.update_idletasks()
        
        # Auto-hide after delay (only if successful)
        if success:
            self.parent.after(3000, self.hide)
    
    def hide(self):
        """Hide the progress UI"""
        self.progress_frame.pack_forget()
        self.cancel_requested = False
    
    def _on_cancel_clicked(self):
        """Handle cancel button click"""
        self.cancel_requested = True
        self.cancel_button.config(state=tk.DISABLED)
        self.status_label.config(text="Cancelling...")
        self.parent.update_idletasks()
    
    def is_cancelled(self):
        """
        Check if operation was cancelled.
        
        Returns:
            True if cancel was requested
        """
        return self.cancel_requested
    
    def _format_time(self, seconds):
        """
        Format elapsed time as string.
        
        Args:
            seconds: Time in seconds
            
        Returns:
            Formatted string like "1.2s" or "1m 23s"
        """
        if seconds < 60:
            return f"{seconds:.1f}s"
        else:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
