"""
Dependency checker for pzmapdzi2img

Automatically checks for and offers to install missing dependencies.
"""
import sys
import subprocess
from pathlib import Path


def check_python_version():
    """Check if Python version meets minimum requirements (3.8+)"""
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    
    if version.major >= 3 and version.minor >= 8:
        return True, f"Python {version_str}"
    else:
        return False, f"Python {version_str} (requires 3.8+)"


def check_pillow():
    """Check if Pillow is installed with required version"""
    try:
        import PIL
        from PIL import Image
        # Check WebP support
        if not hasattr(Image, 'open'):
            return False, "Pillow installed but corrupted"
        return True, f"Pillow {PIL.__version__}"
    except ImportError:
        return False, "Pillow not installed"


def check_tkinter():
    """Check if tkinter is available"""
    try:
        import tkinter
        return True, "tkinter available"
    except ImportError:
        return False, "tkinter not installed (requires Python with tcl/tk support)"


def install_package(package_name):
    """
    Install a package using pip
    
    Args:
        package_name: Name of package to install (e.g., 'Pillow>=10.0.0')
    
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        print(f"\nInstalling {package_name}...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", package_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return True, f"Successfully installed {package_name}"
    except subprocess.CalledProcessError as e:
        return False, f"Failed to install {package_name}: {e}"
    except Exception as e:
        return False, f"Error during installation: {e}"


def check_all_dependencies():
    """
    Check all required dependencies
    
    Returns:
        tuple: (all_ok: bool, results: dict)
    """
    results = {
        'Python': check_python_version(),
        'Pillow': check_pillow(),
        'tkinter': check_tkinter(),
    }
    
    all_ok = all(status for status, _ in results.values())
    return all_ok, results


def prompt_install_missing():
    """
    Check dependencies and prompt user to install missing ones
    
    Returns:
        bool: True if all dependencies are available, False otherwise
    """
    print("=" * 60)
    print("Checking dependencies...")
    print("=" * 60)
    
    all_ok, results = check_all_dependencies()
    
    # Display status
    for package, (status, message) in results.items():
        icon = "✓" if status else "✗"
        print(f"{icon} {package}: {message}")
    
    if all_ok:
        print("\n✓ All dependencies satisfied!")
        print("=" * 60)
        return True
    
    print("\n" + "=" * 60)
    print("Some dependencies are missing.")
    print("=" * 60)
    
    # Check for Python version issues (can't auto-fix)
    if not results['Python'][0]:
        print("\n⚠ Python version is too old!")
        print("This application requires Python 3.8 or newer.")
        print(f"You have: {results['Python'][1]}")
        print("\nTo fix this:")
        print("1. Download Python 3.8+ from python.org")
        print("2. Install it and ensure it's in your PATH")
        print("\nPress Enter to exit...")
        input()
        return False
    
    # Check if tkinter is missing (can't be installed via pip)
    if not results['tkinter'][0]:
        print("\n⚠ tkinter is not available!")
        print("tkinter is part of Python's standard library but requires tcl/tk.")
        print("\nTo fix this:")
        print("1. Reinstall Python from python.org")
        print("2. During installation, ensure 'tcl/tk and IDLE' is checked")
        print("\nPress Enter to exit...")
        input()
        return False
    
    # Offer to install missing pip packages
    missing_packages = []
    if not results['Pillow'][0]:
        missing_packages.append('Pillow>=10.0.0')
    
    if missing_packages:
        print(f"\nMissing packages: {', '.join(missing_packages)}")
        response = input("\nWould you like to install them now? (y/n): ").strip().lower()
        
        if response in ['y', 'yes']:
            all_installed = True
            for package in missing_packages:
                success, message = install_package(package)
                print(message)
                if not success:
                    all_installed = False
            
            if all_installed:
                print("\n✓ All packages installed successfully!")
                print("=" * 60)
                return True
            else:
                print("\n✗ Some packages failed to install.")
                print("Please install them manually using:")
                print(f"  pip install {' '.join(missing_packages)}")
                print("\nPress Enter to exit...")
                input()
                return False
        else:
            print("\nCannot continue without required dependencies.")
            print("To install manually, run:")
            print(f"  pip install {' '.join(missing_packages)}")
            print("\nPress Enter to exit...")
            input()
            return False
    
    return False


if __name__ == "__main__":
    # Test the dependency checker
    if prompt_install_missing():
        print("\nReady to run!")
    else:
        print("\nPlease install missing dependencies and try again.")
