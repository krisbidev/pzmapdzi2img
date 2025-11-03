"""
Image Stitcher

Stitches DZI tiles into complete map images.
"""

from pathlib import Path
from typing import Union
from PIL import Image
from .dzi_parser import parse_dzi
from .pyramid import build_pyramid, get_max_level
from .tile_loader import load_tiles_for_level, get_tile_bounds


def stitch_single_map(
    map_path: Union[str, Path],
    layer: int,
    level: int,
    output_path: Union[str, Path],
    format: str = None
) -> Path:
    """
    Stitch all tiles for a single map layer at a specific zoom level.
    
    This is the basic stitching function for a single map. It loads all tiles
    for the specified layer and level, then stitches them into a single image.
    
    Args:
        map_path: Path to map folder (e.g., 'out/html/map_data/base_top')
        layer: Layer number (0-7 for Build 41)
        level: Zoom level (0 = smallest, max_level = full resolution)
        output_path: Where to save the stitched image
        format: Output format ('PNG', 'JPEG', 'WEBP'). Auto-detected from extension if None.
        
    Returns:
        Path to the saved output file
        
    Raises:
        FileNotFoundError: If map_path or required files don't exist
        ValueError: If layer or level are invalid
        IOError: If image cannot be saved
        
    Example:
        >>> stitch_single_map('out/html/map_data/base_top', 0, 15, 'output.png')
        PosixPath('output.png')
    """
    map_path = Path(map_path)
    output_path = Path(output_path)
    
    # Validate map folder exists
    if not map_path.exists():
        raise FileNotFoundError(f"Map folder not found: {map_path}")
    
    # Read DZI metadata to get dimensions
    dzi_file = map_path / f"layer{layer}.dzi"
    if not dzi_file.exists():
        raise FileNotFoundError(f"DZI file not found: {dzi_file}. Layer {layer} may not exist for this map.")
    
    dzi_info = parse_dzi(dzi_file)
    
    # Build pyramid to verify level is valid
    pyramid = build_pyramid(dzi_info['width'], dzi_info['height'])
    max_level = get_max_level(dzi_info['width'], dzi_info['height'])
    
    if level < 0 or level > max_level:
        raise ValueError(
            f"Invalid level {level}. Must be 0-{max_level} for this map "
            f"(dimensions: {dzi_info['width']}×{dzi_info['height']})"
        )
    
    # Get dimensions at this level
    level_width, level_height = pyramid[level]
    
    print(f"Stitching map: {map_path.name}")
    print(f"  Layer: {layer}, Level: {level}")
    print(f"  Dimensions: {level_width}×{level_height} pixels")
    
    # Load all tiles for this level
    tiles = load_tiles_for_level(map_path, layer, level)
    
    if not tiles:
        raise ValueError(
            f"No tiles found for layer {layer}, level {level}. "
            f"Check if tiles exist in {map_path}/layer{layer}_files/{level}/"
        )
    
    print(f"  Found {len(tiles)} tiles")
    
    # Get tile bounds to determine actual coverage
    bounds = get_tile_bounds(tiles)
    print(f"  Tile grid: {bounds['cols']}×{bounds['rows']} tiles")
    print(f"  Tile coordinates: ({bounds['min_x']},{bounds['min_y']}) to ({bounds['max_x']},{bounds['max_y']})")
    
    # Calculate output image dimensions
    # The tiles might not start at (0,0), so we need to account for the offset
    tile_size = dzi_info['tile_size']
    
    # Calculate actual pixel dimensions based on tile coverage
    # Width: from leftmost tile to rightmost tile + tile width
    # Height: from topmost tile to bottommost tile + tile height
    
    # Get rightmost and bottommost tile dimensions
    rightmost_tiles = [t for t in tiles if t['x'] == bounds['max_x']]
    bottommost_tiles = [t for t in tiles if t['y'] == bounds['max_y']]
    
    # Use actual tile dimensions (edge tiles may be smaller than tile_size)
    rightmost_width = max(t['image'].size[0] for t in rightmost_tiles)
    bottommost_height = max(t['image'].size[1] for t in bottommost_tiles)
    
    # Calculate total dimensions
    output_width = bounds['min_x'] * tile_size + (bounds['cols'] - 1) * tile_size + rightmost_width
    output_height = bounds['min_y'] * tile_size + (bounds['rows'] - 1) * tile_size + bottommost_height
    
    print(f"  Output size: {output_width}×{output_height} pixels")
    
    # Create output canvas
    output_image = Image.new('RGBA', (output_width, output_height), (0, 0, 0, 0))
    
    # Paste each tile into the output image
    print(f"  Stitching tiles...")
    for tile in tiles:
        tile_img = tile['image']
        tile_x = tile['x']
        tile_y = tile['y']
        
        # Calculate pixel position
        pixel_x = tile_x * tile_size
        pixel_y = tile_y * tile_size
        
        # Paste with alpha compositing
        output_image.alpha_composite(tile_img, (pixel_x, pixel_y))
    
    # Determine output format
    if format is None:
        # Auto-detect from file extension
        format = output_path.suffix.upper().lstrip('.')
        if not format:
            format = 'PNG'  # Default to PNG
    
    # Normalize format names (Pillow uses 'JPEG' not 'JPG')
    format = format.upper()
    if format == 'JPG':
        format = 'JPEG'
    
    # Create output directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save the output
    print(f"  Saving to {output_path}...")
    
    # Handle format-specific options
    save_kwargs = {}
    if format in ('JPEG',):
        # JPEG doesn't support transparency, convert to RGB
        if output_image.mode == 'RGBA':
            # Create white background
            background = Image.new('RGB', output_image.size, (255, 255, 255))
            background.paste(output_image, mask=output_image.split()[3])  # Use alpha as mask
            output_image = background
        save_kwargs['quality'] = 95
        save_kwargs['optimize'] = True
    elif format == 'WEBP':
        save_kwargs['quality'] = 95
        save_kwargs['method'] = 6  # Best compression
    elif format == 'PNG':
        save_kwargs['optimize'] = True
    
    output_image.save(output_path, format=format, **save_kwargs)
    
    print(f"✓ Complete! Saved to {output_path}")
    print(f"  Final size: {output_image.size[0]}×{output_image.size[1]} pixels")
    
    return output_path
