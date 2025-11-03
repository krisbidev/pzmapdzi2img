"""
Pyramid Calculator

Calculates DZI pyramid levels and dimensions for Deep Zoom Image format.

The DZI pyramid is a multi-resolution representation where each level
is HALF the resolution of the level above it, stopping at 1x1 pixel.
"""

import math
from typing import List, Tuple, Dict, Any
import logging

logger = logging.getLogger(__name__)


def build_pyramid(width: int, height: int) -> List[Tuple[int, int]]:
    """
    Build a complete DZI pyramid from full resolution down to 1x1 pixel.
    
    The pyramid is built by repeatedly halving dimensions (rounding up)
    until reaching 1x1 pixel. Level 0 is always 1x1, and the max level
    is the original dimensions.
    
    Args:
        width: Full resolution width in pixels (must be positive)
        height: Full resolution height in pixels (must be positive)
        
    Returns:
        List of (width, height) tuples, indexed by level.
        Level 0 is (1, 1), max level is (width, height).
        
    Raises:
        ValueError: If width or height are not positive
        
    Example:
        >>> pyramid = build_pyramid(19800, 15900)
        >>> len(pyramid)
        16
        >>> pyramid[0]   # Level 0 (lowest zoom)
        (1, 1)
        >>> pyramid[15]  # Level 15 (highest zoom, full resolution)
        (19800, 15900)
        >>> pyramid[9]   # Level 9
        (310, 249)
    """
    if width <= 0 or height <= 0:
        raise ValueError(
            f"Invalid dimensions for pyramid: {width}x{height}\n"
            f"Width and height must be positive integers"
        )
    
    # Build pyramid from top (full size) down to (1, 1)
    pyramid = [(width, height)]
    
    while pyramid[-1] != (1, 1):
        w, h = pyramid[-1]
        # Half size, rounding up (ensures we reach 1x1 eventually)
        w = (w + 1) // 2
        h = (h + 1) // 2
        pyramid.append((w, h))
    
    # Reverse so level 0 is smallest (1x1)
    pyramid.reverse()
    
    return pyramid


def calculate_num_levels(width: int, height: int) -> int:
    """
    Calculate the number of levels in a DZI pyramid.
    
    This is approximately log₂(max(width, height)) + 1, but the exact
    value depends on the rounding behavior of the pyramid algorithm.
    
    Args:
        width: Full resolution width in pixels
        height: Full resolution height in pixels
        
    Returns:
        Number of levels (including level 0)
        
    Example:
        >>> calculate_num_levels(19800, 15900)
        16
        >>> calculate_num_levels(300, 1200)
        12
        >>> calculate_num_levels(1200, 1200)
        12
    """
    return len(build_pyramid(width, height))


def get_max_level(width: int, height: int) -> int:
    """
    Get the maximum (highest zoom) level index for given dimensions.
    
    Args:
        width: Full resolution width in pixels
        height: Full resolution height in pixels
        
    Returns:
        Maximum level index (0-based)
        
    Example:
        >>> get_max_level(19800, 15900)
        15
        >>> get_max_level(300, 1200)
        11
    """
    return calculate_num_levels(width, height) - 1


def calculate_tiles_for_level(
    level_width: int,
    level_height: int,
    tile_size: int = 300
) -> Tuple[int, int]:
    """
    Calculate the number of tiles (columns x rows) for a pyramid level.
    
    Tiles are tile_size × tile_size, except for edge tiles which may
    be smaller.
    
    Args:
        level_width: Width of this level in pixels
        level_height: Height of this level in pixels
        tile_size: Size of tiles (default 300 for Build 41)
        
    Returns:
        Tuple of (num_cols, num_rows)
        
    Example:
        >>> calculate_tiles_for_level(19800, 15900, 300)
        (66, 53)
        >>> calculate_tiles_for_level(310, 249, 300)
        (2, 1)
        >>> calculate_tiles_for_level(155, 125, 300)
        (1, 1)
    """
    if tile_size <= 0:
        raise ValueError(f"tile_size must be positive, got {tile_size}")
    
    # Divide and round up (ceil)
    num_cols = (level_width + tile_size - 1) // tile_size
    num_rows = (level_height + tile_size - 1) // tile_size
    
    return (num_cols, num_rows)


def get_pyramid_info(
    width: int,
    height: int,
    tile_size: int = 300,
    skip: int = 0
) -> Dict[str, Any]:
    """
    Get comprehensive pyramid information for a map.
    
    Args:
        width: Full resolution width in pixels
        height: Full resolution height in pixels
        tile_size: Size of tiles (default 300 for Build 41)
        skip: Number of TOP levels omitted (from map_info.json)
        
    Returns:
        Dictionary with keys:
            - pyramid: List of (width, height) for each level
            - num_levels: Total number of levels
            - max_level: Highest level index (accounting for skip)
            - min_level: Lowest level available (= skip)
            - tiles_per_level: Dict of {level: (cols, rows)}
            - total_tiles: Total number of tiles across all available levels
            
    Raises:
        ValueError: If skip is negative or >= num_levels
        
    Example:
        >>> info = get_pyramid_info(19800, 15900, 300, skip=0)
        >>> info['num_levels']
        16
        >>> info['max_level']
        15
        >>> info['min_level']
        0
        >>> info['tiles_per_level'][15]
        (66, 53)
    """
    if skip < 0:
        raise ValueError(f"skip must be non-negative, got {skip}")
    
    pyramid = build_pyramid(width, height)
    num_levels = len(pyramid)
    
    if skip >= num_levels:
        raise ValueError(
            f"skip={skip} is >= num_levels={num_levels}\n"
            f"Cannot skip more levels than exist in the pyramid"
        )
    
    # Calculate tiles for each level
    tiles_per_level = {}
    total_tiles = 0
    
    for level in range(skip, num_levels):
        w, h = pyramid[level]
        cols, rows = calculate_tiles_for_level(w, h, tile_size)
        tiles_per_level[level] = (cols, rows)
        total_tiles += cols * rows
    
    # Log warning if skip is used
    if skip > 0:
        logger.warning(
            f"Pyramid has skip={skip}, omitting top {skip} levels\n"
            f"Available levels: {skip} to {num_levels - 1} (instead of 0 to {num_levels - 1})"
        )
    
    return {
        'pyramid': pyramid,
        'num_levels': num_levels,
        'max_level': num_levels - 1,  # Actual max level in pyramid
        'min_level': skip,  # First available level (accounting for skip)
        'tiles_per_level': tiles_per_level,
        'total_tiles': total_tiles
    }


def validate_pyramid_consistency(pyramids: Dict[str, List[Tuple[int, int]]]) -> bool:
    """
    Validate that multiple pyramids have the same number of levels.
    
    This is important when stitching multiple maps together - they
    must all have the same pyramid structure to align properly.
    
    Args:
        pyramids: Dictionary of {map_name: pyramid_list}
        
    Returns:
        True if all pyramids have same number of levels
        
    Raises:
        ValueError: If pyramids have different numbers of levels
        
    Example:
        >>> pyramids = {
        ...     'base': build_pyramid(19800, 15900),
        ...     'mod1': build_pyramid(4800, 7200),
        ... }
        >>> validate_pyramid_consistency(pyramids)
        Traceback (most recent call last):
        ValueError: Maps have inconsistent pyramid levels...
    """
    if not pyramids:
        raise ValueError("No pyramids provided for consistency check")
    
    level_counts = {name: len(pyr) for name, pyr in pyramids.items()}
    unique_counts = set(level_counts.values())
    
    if len(unique_counts) > 1:
        details = '\n'.join(
            f"  {name}: {count} levels" for name, count in level_counts.items()
        )
        raise ValueError(
            f"Maps have inconsistent pyramid levels (cannot stitch together):\n{details}\n"
            f"All maps must have the same number of zoom levels.\n"
            f"This usually means maps have very different dimensions."
        )
    
    return True

