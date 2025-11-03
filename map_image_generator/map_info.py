"""
Map Info JSON Reader

Reads and validates map_info.json metadata files from pzmap2dzi output.
"""

import json
from pathlib import Path
from typing import Dict, Union, Any
import logging

logger = logging.getLogger(__name__)


def read_map_info(map_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Read and validate map_info.json from a map folder.
    
    Args:
        map_path: Path to the map folder (containing map_info.json)
        
    Returns:
        Dictionary with keys:
            - w (int): Full width in pixels
            - h (int): Full height in pixels
            - x0 (int): Origin X coordinate (can be negative!)
            - y0 (int): Origin Y coordinate (can be negative!)
            - cell_size (int): Cell size in pixels (always 300 for Build 41)
            - skip (int): Number of TOP zoom levels omitted
            - sqr (int): Square size (pixels per game cell), defaults to 1
            - cell_rects (list): List of map coverage rectangles [x, y, w, h]
            - pz_version (str): Project Zomboid version (B41, B42, etc.)
            - [other fields preserved as-is]
            
    Raises:
        FileNotFoundError: If map_info.json doesn't exist
        ValueError: If required fields are missing
        json.JSONDecodeError: If file is not valid JSON
        
    Example:
        >>> info = read_map_info("out/html/map_data/base_top")
        >>> print(info['w'], info['h'], info['sqr'])
        19800 15900 1
    """
    map_path = Path(map_path)
    info_path = map_path / "map_info.json"
    
    if not info_path.exists():
        raise FileNotFoundError(
            f"map_info.json not found in: {map_path}\n"
            f"Expected at: {info_path}"
        )
    
    try:
        with open(info_path, 'r', encoding='utf-8') as f:
            info = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {info_path}: {e}")
    
    # Validate required fields
    required = ['w', 'h', 'x0', 'y0', 'cell_size']
    missing = [k for k in required if k not in info]
    if missing:
        raise ValueError(
            f"Missing required fields in {info_path}: {', '.join(missing)}\n"
            f"Required: {', '.join(required)}"
        )
    
    # Handle sqr field - may be missing in older versions
    if 'sqr' not in info:
        logger.warning(f"'sqr' field missing in {info_path}, defaulting to 1")
        info['sqr'] = 1
    
    # Validate sqr value
    sqr = info['sqr']
    if sqr != 1:
        logger.warning(
            f"Non-standard sqr value in {map_path.name}: sqr={sqr}\n"
            f"This means each game cell = {sqr}×{sqr} pixels\n"
            f"Tile size = {sqr} × {info['cell_size']} = {sqr * info['cell_size']} pixels per cell"
        )
    
    # Validate skip field (default to 0 if missing)
    if 'skip' not in info:
        logger.warning(f"'skip' field missing in {info_path}, defaulting to 0")
        info['skip'] = 0
    
    # Validate numeric fields are actually numbers
    numeric_fields = ['w', 'h', 'x0', 'y0', 'cell_size', 'skip', 'sqr']
    for field in numeric_fields:
        if field in info:
            try:
                info[field] = int(info[field])
            except (ValueError, TypeError):
                raise ValueError(
                    f"Field '{field}' must be numeric in {info_path}, got: {info[field]}"
                )
    
    # Validate dimensions are positive
    if info['w'] <= 0 or info['h'] <= 0:
        raise ValueError(
            f"Invalid dimensions in {info_path}: w={info['w']}, h={info['h']}\n"
            f"Width and height must be positive"
        )
    
    # Validate cell_size is 300 (Build 41 standard)
    if info['cell_size'] != 300:
        logger.warning(
            f"Non-standard cell_size in {map_path.name}: {info['cell_size']}\n"
            f"Expected 300 for Build 41"
        )
    
    return info


def validate_maps_consistency(maps: Dict[str, Dict[str, Any]]) -> bool:
    """
    Validate that multiple maps can be stitched together consistently.
    
    Checks:
    - All maps have the same sqr value
    - All maps are Build 41 (no B42 mixing)
    - All maps have the same cell_size
    
    Args:
        maps: Dictionary of {map_name: map_info_dict}
        
    Returns:
        True if all maps are consistent
        
    Raises:
        ValueError: If maps are inconsistent
        
    Example:
        >>> maps = {
        ...     'base_top': read_map_info('out/html/map_data/base_top'),
        ...     'mod_map': read_map_info('out/html/map_data/mod_maps/SomeMap/base_top')
        ... }
        >>> validate_maps_consistency(maps)
        True
    """
    if not maps:
        raise ValueError("No maps provided for consistency check")
    
    # Check sqr consistency
    sqr_values = {info['sqr'] for info in maps.values()}
    if len(sqr_values) > 1:
        details = '\n'.join(f"  {name}: sqr={info['sqr']}" for name, info in maps.items())
        raise ValueError(
            f"Maps have inconsistent sqr values (cannot stitch together):\n{details}\n"
            f"All maps must have the same sqr value in map_info.json"
        )
    
    # Check cell_size consistency
    cell_sizes = {info['cell_size'] for info in maps.values()}
    if len(cell_sizes) > 1:
        details = '\n'.join(f"  {name}: cell_size={info['cell_size']}" for name, info in maps.items())
        raise ValueError(
            f"Maps have inconsistent cell_size values:\n{details}\n"
            f"All maps must have the same cell_size"
        )
    
    # Check Build 41 only (no B42)
    for name, info in maps.items():
        pz_version = info.get('pz_version', 'unknown')
        if pz_version == 'B42':
            raise ValueError(
                f"Map '{name}' is Build 42. This tool only supports Build 41.\n"
                f"Build 42 uses different layer structure (layer-1 to layer8 instead of layer0 to layer7)"
            )
    
    return True


def get_map_bounds(map_info: Dict[str, Any]) -> Dict[str, int]:
    """
    Calculate the pixel bounds of a map.
    
    Args:
        map_info: Dictionary from read_map_info()
        
    Returns:
        Dictionary with keys:
            - min_x: Leftmost pixel coordinate
            - min_y: Topmost pixel coordinate
            - max_x: Rightmost pixel coordinate
            - max_y: Bottommost pixel coordinate
            - width: Total width in pixels
            - height: Total height in pixels
            
    Example:
        >>> info = read_map_info("out/html/map_data/base_top")
        >>> bounds = get_map_bounds(info)
        >>> print(bounds['width'], bounds['height'])
        19800 15900
    """
    min_x = map_info['x0']
    min_y = map_info['y0']
    max_x = min_x + map_info['w']
    max_y = min_y + map_info['h']
    
    return {
        'min_x': min_x,
        'min_y': min_y,
        'max_x': max_x,
        'max_y': max_y,
        'width': map_info['w'],
        'height': map_info['h']
    }

