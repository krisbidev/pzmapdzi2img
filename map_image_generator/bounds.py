"""
Global bounds calculator for multi-map stitching.

This module calculates the bounding box that encompasses multiple maps
with different positions and dimensions in world space.
"""

from pathlib import Path
from typing import List, Dict, Any
from .map_info import read_map_info


def calculate_global_bounds(map_paths: List[Path], layer: int = 0) -> Dict[str, Any]:
    """
    Calculate the global bounding box for multiple maps.
    
    Args:
        map_paths: List of paths to map directories (containing map_info.json)
        layer: Layer number (used for validation, not calculation)
        
    Returns:
        Dictionary with keys:
        - min_x: Leftmost world coordinate (pixels)
        - min_y: Topmost world coordinate (pixels)
        - max_x: Rightmost world coordinate (pixels)
        - max_y: Bottommost world coordinate (pixels)
        - width: Total width (max_x - min_x)
        - height: Total height (max_y - min_y)
        - maps: List of dicts with per-map info (name, x0, y0, w, h, offset_x, offset_y)
        
    Raises:
        FileNotFoundError: If map_info.json not found in any map path
        ValueError: If no valid maps found or layer invalid
    """
    if not map_paths:
        raise ValueError("No map paths provided")
    
    # Load all map metadata
    maps_data = []
    for map_path in map_paths:
        try:
            info = read_map_info(map_path)
            maps_data.append({
                'name': map_path.name,
                'path': map_path,
                'info': info
            })
        except FileNotFoundError:
            raise FileNotFoundError(f"map_info.json not found in {map_path}")
    
    if not maps_data:
        raise ValueError("No valid maps found")
    
    # Calculate global bounding box
    min_x = min(m['info']['x0'] for m in maps_data)
    min_y = min(m['info']['y0'] for m in maps_data)
    max_x = max(m['info']['x0'] + m['info']['w'] for m in maps_data)
    max_y = max(m['info']['y0'] + m['info']['h'] for m in maps_data)
    
    global_width = max_x - min_x
    global_height = max_y - min_y
    
    # Calculate offset for each map (where it should be placed in global canvas)
    maps_with_offsets = []
    for m in maps_data:
        offset_x = m['info']['x0'] - min_x
        offset_y = m['info']['y0'] - min_y
        maps_with_offsets.append({
            'name': m['name'],
            'x0': m['info']['x0'],
            'y0': m['info']['y0'],
            'w': m['info']['w'],
            'h': m['info']['h'],
            'offset_x': offset_x,
            'offset_y': offset_y
        })
    
    return {
        'min_x': min_x,
        'min_y': min_y,
        'max_x': max_x,
        'max_y': max_y,
        'width': global_width,
        'height': global_height,
        'maps': maps_with_offsets
    }


def get_map_offset(map_info: Dict[str, Any], global_bounds: Dict[str, Any]) -> tuple[int, int]:
    """
    Calculate where a map should be positioned in the global canvas.
    
    Args:
        map_info: Dictionary from read_map_info() with 'x0' and 'y0' keys
        global_bounds: Dictionary from calculate_global_bounds()
        
    Returns:
        Tuple of (offset_x, offset_y) in pixels
    """
    offset_x = map_info['x0'] - global_bounds['min_x']
    offset_y = map_info['y0'] - global_bounds['min_y']
    return (offset_x, offset_y)


def validate_map_compatibility(map_paths: List[Path]) -> Dict[str, Any]:
    """
    Validate that maps can be stitched together.
    
    Checks:
    - All maps have same sqr value
    - All maps have same cell_size
    - All maps are same pz_version (Build 41 only)
    
    Args:
        map_paths: List of paths to map directories
        
    Returns:
        Dictionary with validation results:
        - compatible: True if all checks pass
        - sqr: Common sqr value (or None if mismatch)
        - cell_size: Common cell_size (or None if mismatch)
        - pz_version: Common version (or None if mismatch)
        - warnings: List of warning messages
        - errors: List of error messages
        
    Raises:
        FileNotFoundError: If map_info.json not found
    """
    if not map_paths:
        return {
            'compatible': False,
            'sqr': None,
            'cell_size': None,
            'pz_version': None,
            'warnings': [],
            'errors': ['No map paths provided']
        }
    
    # Load all map metadata
    maps_info = []
    for map_path in map_paths:
        info = read_map_info(map_path)
        maps_info.append({'name': map_path.name, 'info': info})
    
    # Check sqr values
    sqr_values = set(m['info']['sqr'] for m in maps_info)
    sqr_compatible = len(sqr_values) == 1
    sqr = list(sqr_values)[0] if sqr_compatible else None
    
    # Check cell_size values
    cell_size_values = set(m['info']['cell_size'] for m in maps_info)
    cell_size_compatible = len(cell_size_values) == 1
    cell_size = list(cell_size_values)[0] if cell_size_compatible else None
    
    # Check pz_version values
    version_values = set(m['info']['pz_version'] for m in maps_info)
    version_compatible = len(version_values) == 1
    pz_version = list(version_values)[0] if version_compatible else None
    
    # Build warnings and errors
    warnings = []
    errors = []
    
    if not sqr_compatible:
        errors.append(f"Maps have different sqr values: {sqr_values}. Cannot stitch together.")
    
    if not cell_size_compatible:
        errors.append(f"Maps have different cell_size values: {cell_size_values}. Cannot stitch together.")
    
    if not version_compatible:
        warnings.append(f"Maps have different PZ versions: {version_values}. May have compatibility issues.")
    
    if pz_version and pz_version != 'B41':
        warnings.append(f"Non-B41 version detected: {pz_version}. This tool only supports Build 41.")
    
    compatible = len(errors) == 0
    
    return {
        'compatible': compatible,
        'sqr': sqr,
        'cell_size': cell_size,
        'pz_version': pz_version,
        'warnings': warnings,
        'errors': errors
    }
