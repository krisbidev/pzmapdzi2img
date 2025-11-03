"""
Tile Loader

Loads individual tile images from disk with proper format handling.
"""

import re
from pathlib import Path
from typing import Union, Tuple, List, Dict, Any, Optional
import logging

from PIL import Image

logger = logging.getLogger(__name__)


def load_tile(tile_path: Union[str, Path]) -> Image.Image:
    """
    Load a single tile image from disk.
    
    Automatically converts to RGBA mode for consistent compositing.
    Handles WebP, PNG, and JPG formats.
    
    Args:
        tile_path: Path to tile image file
        
    Returns:
        PIL Image in RGBA mode
        
    Raises:
        FileNotFoundError: If tile file doesn't exist
        IOError: If image cannot be loaded
        
    Example:
        >>> tile = load_tile('out/html/map_data/base_top/layer0_files/15/0_16.webp')
        >>> print(tile.size, tile.mode)
        (300, 249) RGBA
    """
    tile_path = Path(tile_path)
    
    if not tile_path.exists():
        raise FileNotFoundError(f"Tile file not found: {tile_path}")
    
    try:
        with Image.open(tile_path) as img:
            # Load image data into memory and convert to RGBA
            # This ensures the file is closed and all tiles have alpha channel
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # Force load into memory before closing file
            img.load()
            
            return img
        
    except Exception as e:
        raise IOError(f"Failed to load tile {tile_path}: {e}")


def parse_tile_coords(filename: str) -> Tuple[int, int]:
    """
    Parse tile coordinates from filename.
    
    Expected format: {x}_{y}.{ext}
    Example: "5_10.webp" → (5, 10)
    
    Args:
        filename: Tile filename (with or without path)
        
    Returns:
        Tuple of (x, y) coordinates
        
    Raises:
        ValueError: If filename doesn't match expected format
        
    Example:
        >>> x, y = parse_tile_coords("5_10.webp")
        >>> print(x, y)
        5 10
    """
    # Extract just the filename if full path provided
    filename = Path(filename).name
    
    # Match pattern: digits_digits.extension
    match = re.match(r'(\d+)_(\d+)\.\w+$', filename)
    
    if not match:
        raise ValueError(
            f"Invalid tile filename format: {filename}\n"
            f"Expected format: {{x}}_{{y}}.{{ext}} (e.g., '5_10.webp')"
        )
    
    x = int(match.group(1))
    y = int(match.group(2))
    
    return (x, y)


def get_tile_path(
    map_path: Union[str, Path],
    layer: int,
    level: int,
    x: int,
    y: int,
    format: str = 'webp'
) -> Path:
    """
    Construct the path to a specific tile.
    
    Args:
        map_path: Path to map folder (e.g., base_top/)
        layer: Layer number (0-7 for Build 41)
        level: Zoom level number
        x: Tile column coordinate
        y: Tile row coordinate
        format: Image format extension (webp, png, jpg)
        
    Returns:
        Path to tile file
        
    Example:
        >>> path = get_tile_path('out/html/map_data/base_top', 0, 15, 5, 10)
        >>> print(path)
        out/html/map_data/base_top/layer0_files/15/5_10.webp
    """
    map_path = Path(map_path)
    return map_path / f"layer{layer}_files" / str(level) / f"{x}_{y}.{format}"


def load_tiles_for_level(
    map_path: Union[str, Path],
    layer: int,
    level: int,
    tile_format: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Load all tiles for a specific layer and level.
    
    Scans the level directory and loads all tiles found.
    Automatically detects format if not specified.
    
    Args:
        map_path: Path to map folder
        layer: Layer number (0-7 for Build 41)
        level: Zoom level number
        tile_format: Optional format filter ('webp', 'png', 'jpg')
        
    Returns:
        List of dictionaries with keys:
            - x: Tile column coordinate
            - y: Tile row coordinate
            - image: PIL Image in RGBA mode
            - path: Path to tile file
            - size: Tuple of (width, height)
            
    Example:
        >>> tiles = load_tiles_for_level('out/html/map_data/base_top', 0, 15)
        >>> print(f"Loaded {len(tiles)} tiles")
        Loaded 3498 tiles
        >>> print(tiles[0])
        {'x': 0, 'y': 16, 'image': <PIL.Image...>, 'path': Path(...), 'size': (300, 249)}
    """
    map_path = Path(map_path)
    tile_folder = map_path / f"layer{layer}_files" / str(level)
    
    if not tile_folder.exists():
        logger.warning(f"Tile folder not found: {tile_folder}")
        return []
    
    tiles = []
    
    # Determine which extensions to scan
    if tile_format:
        extensions = [f".{tile_format}"]
    else:
        extensions = ['.webp', '.png', '.jpg', '.jpeg']
    
    # Scan for tile files
    for tile_file in tile_folder.iterdir():
        if tile_file.is_file() and tile_file.suffix.lower() in extensions:
            try:
                # Parse coordinates from filename
                x, y = parse_tile_coords(tile_file.name)
                
                # Load the image
                img = load_tile(tile_file)
                
                tiles.append({
                    'x': x,
                    'y': y,
                    'image': img,
                    'path': tile_file,
                    'size': img.size
                })
                
            except (ValueError, IOError) as e:
                logger.warning(f"Skipping invalid tile {tile_file.name}: {e}")
    
    # Sort by coordinates (y first, then x) for predictable order
    tiles.sort(key=lambda t: (t['y'], t['x']))
    
    logger.info(f"Loaded {len(tiles)} tiles from {tile_folder}")
    return tiles


def get_tile_bounds(tiles: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Calculate the bounding box of a set of tiles.
    
    Args:
        tiles: List of tile dictionaries from load_tiles_for_level()
        
    Returns:
        Dictionary with keys:
            - min_x: Leftmost tile column
            - min_y: Topmost tile row
            - max_x: Rightmost tile column
            - max_y: Bottommost tile row
            - cols: Number of columns
            - rows: Number of rows
            
    Example:
        >>> tiles = load_tiles_for_level('out/html/map_data/base_top', 0, 15)
        >>> bounds = get_tile_bounds(tiles)
        >>> print(bounds)
        {'min_x': 0, 'min_y': 16, 'max_x': 65, 'max_y': 68, 'cols': 66, 'rows': 53}
    """
    if not tiles:
        return {
            'min_x': 0, 'min_y': 0, 'max_x': 0, 'max_y': 0,
            'cols': 0, 'rows': 0
        }
    
    x_coords = [t['x'] for t in tiles]
    y_coords = [t['y'] for t in tiles]
    
    min_x = min(x_coords)
    max_x = max(x_coords)
    min_y = min(y_coords)
    max_y = max(y_coords)
    
    return {
        'min_x': min_x,
        'min_y': min_y,
        'max_x': max_x,
        'max_y': max_y,
        'cols': max_x - min_x + 1,
        'rows': max_y - min_y + 1
    }


def check_tile_exists(
    map_path: Union[str, Path],
    layer: int,
    level: int,
    x: int,
    y: int,
    formats: List[str] = None
) -> Optional[Path]:
    """
    Check if a tile file exists, trying multiple formats.
    
    Args:
        map_path: Path to map folder
        layer: Layer number
        level: Zoom level number
        x: Tile column coordinate
        y: Tile row coordinate
        formats: List of formats to try (default: ['webp', 'png', 'jpg'])
        
    Returns:
        Path to tile file if found, None otherwise
        
    Example:
        >>> path = check_tile_exists('out/html/map_data/base_top', 0, 15, 0, 16)
        >>> print(path)
        out/html/map_data/base_top/layer0_files/15/0_16.webp
    """
    if formats is None:
        formats = ['webp', 'png', 'jpg']
    
    map_path = Path(map_path)
    
    for fmt in formats:
        tile_path = get_tile_path(map_path, layer, level, x, y, fmt)
        if tile_path.exists():
            return tile_path
    
    return None

