"""
DZI XML Parser

Parses Microsoft Deep Zoom Image (DZI) XML files to extract pyramid metadata.
DZI format: http://schemas.microsoft.com/deepzoom/2008
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Union


def parse_dzi(dzi_path: Union[str, Path]) -> Dict[str, Union[int, str]]:
    """
    Parse a .dzi XML file and extract metadata.
    
    Args:
        dzi_path: Path to the .dzi file
        
    Returns:
        Dictionary with keys:
            - width (int): Image width in pixels at max level
            - height (int): Image height in pixels at max level
            - tile_size (int): Maximum tile dimension (usually 300)
            - overlap (int): Pixel overlap between adjacent tiles (usually 0)
            - format (str): Image format (webp, jpg, png)
            - xmlns (str): XML namespace
            
    Raises:
        FileNotFoundError: If .dzi file doesn't exist
        ValueError: If .dzi file is malformed or missing required fields
        
    Example:
        >>> info = parse_dzi("out/html/map_data/Muldraugh, KY/layer0.dzi")
        >>> print(info['width'], info['height'], info['format'])
        19800 15900 webp
    """
    dzi_path = Path(dzi_path)
    
    if not dzi_path.exists():
        raise FileNotFoundError(f"DZI file not found: {dzi_path}")
    
    try:
        tree = ET.parse(dzi_path)
        root = tree.getroot()
        
        # Handle XML namespace
        xmlns = root.tag.split('}')[0].strip('{') if '}' in root.tag else ''
        ns = {'dzi': xmlns} if xmlns else {}
        
        # Extract attributes from <Image> element
        tile_size = root.get('TileSize')
        overlap = root.get('Overlap')
        fmt = root.get('Format')
        
        # Extract <Size> element
        if xmlns:
            size_elem = root.find('dzi:Size', ns)
        else:
            size_elem = root.find('Size')
            
        if size_elem is None:
            raise ValueError(f"Missing <Size> element in DZI file: {dzi_path}")
        
        width = size_elem.get('Width')
        height = size_elem.get('Height')
        
        # Validate all required fields are present
        if not all([tile_size, overlap is not None, fmt, width, height]):
            missing = []
            if not tile_size: missing.append('TileSize')
            if overlap is None: missing.append('Overlap')
            if not fmt: missing.append('Format')
            if not width: missing.append('Width')
            if not height: missing.append('Height')
            raise ValueError(
                f"Missing required fields in DZI file {dzi_path}: {', '.join(missing)}"
            )
        
        # Convert to proper types
        return {
            'width': int(width),
            'height': int(height),
            'tile_size': int(tile_size),
            'overlap': int(overlap),
            'format': fmt.lower(),
            'xmlns': xmlns
        }
        
    except ET.ParseError as e:
        raise ValueError(f"Malformed XML in DZI file {dzi_path}: {e}")
    except (ValueError, AttributeError) as e:
        if "invalid literal for int()" in str(e):
            raise ValueError(f"Invalid numeric value in DZI file {dzi_path}: {e}")
        raise


def get_tiles_folder(dzi_path: Union[str, Path]) -> Path:
    """
    Get the tiles folder path for a given .dzi file.
    
    DZI convention: layer0.dzi -> layer0_files/
    
    Args:
        dzi_path: Path to the .dzi file
        
    Returns:
        Path to the tiles folder (may not exist)
        
    Example:
        >>> folder = get_tiles_folder("layer0.dzi")
        >>> print(folder)
        layer0_files
    """
    dzi_path = Path(dzi_path)
    stem = dzi_path.stem  # "layer0" from "layer0.dzi"
    tiles_folder = dzi_path.parent / f"{stem}_files"
    return tiles_folder


def validate_dzi(dzi_path: Union[str, Path]) -> bool:
    """
    Validate that a .dzi file and its tiles folder exist and are readable.
    
    Args:
        dzi_path: Path to the .dzi file
        
    Returns:
        True if valid
        
    Raises:
        FileNotFoundError: If .dzi or tiles folder don't exist
        ValueError: If .dzi file is malformed
        
    Example:
        >>> validate_dzi("out/html/map_data/Muldraugh, KY/layer0.dzi")
        True
    """
    dzi_path = Path(dzi_path)
    
    # Check .dzi file exists and is parseable
    info = parse_dzi(dzi_path)  # Will raise if invalid
    
    # Check tiles folder exists
    tiles_folder = get_tiles_folder(dzi_path)
    if not tiles_folder.exists():
        raise FileNotFoundError(
            f"Tiles folder not found: {tiles_folder}\n"
            f"Expected folder for {dzi_path.name}"
        )
    
    if not tiles_folder.is_dir():
        raise ValueError(f"Tiles path is not a directory: {tiles_folder}")
    
    return True

