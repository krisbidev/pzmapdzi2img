"""
Project Zomboid Map Stitcher - GUI Application

Launch the GUI interface for generating map images from DZI tiles.
"""
import sys
from check_dependencies import prompt_install_missing


if __name__ == "__main__":
    # Check dependencies before starting GUI
    if not prompt_install_missing():
        print("\nExiting due to missing dependencies.")
        sys.exit(1)
    
    # Import and run GUI (import after dependency check)
    from gui.main_window import main
    main()
