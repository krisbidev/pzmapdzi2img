"""
Image Stitcher V2 - Clean implementation after Task #13

This is a streamlined version with all the lessons learned:
- x0/y0 are negative world coordinates (negate them)
- w/h are already in world space (no normalization)
- Tile coordinates don't start at 0 (normalize them)
- Maps have different max levels (calculate per-map zoom)
"""

from pathlib import Path
from typing import Union, List
from PIL import Image
from .dzi_parser import parse_dzi
from .pyramid import build_pyramid, get_max_level
from .tile_loader import load_tiles_for_level, get_tile_bounds
from .bounds import calculate_global_bounds, validate_map_compatibility
from .map_info import read_map_info


def stitch_single_map(
    map_path: Union[str, Path],
    layer: int,
    level: int,
    output_path: Union[str, Path],
    format: str = None
) -> Path:
    """
    Stitch all tiles for a single map layer at a specific zoom level.
    
    Args:
        map_path: Path to map folder (e.g., 'out/html/map_data/base_top')
        layer: Layer number (0-7 for Build 41)
        level: Zoom level (0 = smallest, max_level = full resolution)
        output_path: Where to save the stitched image
        format: Output format ('PNG', 'JPEG', 'WEBP'). Auto-detected if None.
        
    Returns:
        Path to the saved output file
    """
    map_path = Path(map_path)
    output_path = Path(output_path)
    
    if not map_path.exists():
        raise FileNotFoundError(f"Map folder not found: {map_path}")
    
    # Read DZI metadata
    dzi_file = map_path / f"layer{layer}.dzi"
    if not dzi_file.exists():
        raise FileNotFoundError(f"DZI file not found: {dzi_file}")
    
    dzi_info = parse_dzi(dzi_file)
    tile_size = dzi_info['tile_size']
    
    # Validate level
    pyramid = build_pyramid(dzi_info['width'], dzi_info['height'])
    max_level = get_max_level(dzi_info['width'], dzi_info['height'])
    
    if not (0 <= level <= max_level):
        raise ValueError(f"Invalid level {level}. Must be 0-{max_level}")
    
    level_width, level_height = pyramid[level]
    print(f"Stitching {map_path.name}, layer {layer}, level {level}")
    print(f"  Dimensions: {level_width}×{level_height} pixels")
    
    # Load tiles
    tiles = load_tiles_for_level(map_path, layer, level)
    if not tiles:
        raise ValueError(f"No tiles found for layer {layer}, level {level}")
    
    print(f"  Found {len(tiles)} tiles")
    
    # Get tile bounds (tiles don't start at 0!)
    bounds = get_tile_bounds(tiles)
    print(f"  Tile grid: ({bounds['min_x']},{bounds['min_y']}) to ({bounds['max_x']},{bounds['max_y']})")
    
    # Calculate output dimensions
    # Get rightmost and bottommost tile actual sizes (edge tiles may be smaller)
    rightmost = [t for t in tiles if t['x'] == bounds['max_x']]
    bottommost = [t for t in tiles if t['y'] == bounds['max_y']]
    
    rightmost_width = max(t['image'].size[0] for t in rightmost)
    bottommost_height = max(t['image'].size[1] for t in bottommost)
    
    output_width = bounds['min_x'] * tile_size + (bounds['cols'] - 1) * tile_size + rightmost_width
    output_height = bounds['min_y'] * tile_size + (bounds['rows'] - 1) * tile_size + bottommost_height
    
    print(f"  Output: {output_width}×{output_height} pixels")
    
    # Create canvas and paste tiles
    output_image = Image.new('RGBA', (output_width, output_height), (0, 0, 0, 0))
    
    for tile in tiles:
        pixel_x = tile['x'] * tile_size
        pixel_y = tile['y'] * tile_size
        output_image.alpha_composite(tile['image'], (pixel_x, pixel_y))
    
    # Save
    _save_image(output_image, output_path, format)
    print(f"✓ Saved to {output_path}")
    
    return output_path


def stitch_multi_map(
    map_paths: List[Union[str, Path]],
    layer: int,
    level: int,
    output_path: Union[str, Path],
    format: str = None
) -> Path:
    """
    Stitch multiple maps together into a single image.
    
    Maps are processed in order - later maps overlay earlier ones.
    
    Args:
        map_paths: List of paths to map folders
        layer: Layer number (0-7 for Build 41)
        level: Zoom level (0 = smallest, max_level = full resolution)
        output_path: Where to save the stitched image
        format: Output format ('PNG', 'JPEG', 'WEBP'). Auto-detected if None.
        
    Returns:
        Path to the saved output file
    """
    map_paths = [Path(p) for p in map_paths]
    output_path = Path(output_path)
    
    # Validate maps exist
    for map_path in map_paths:
        if not map_path.exists():
            raise FileNotFoundError(f"Map folder not found: {map_path}")
    
    # Validate compatibility
    print("Validating maps...")
    compat = validate_map_compatibility(map_paths)
    if not compat['compatible']:
        raise ValueError("Maps incompatible:\n" + "\n".join(f"  {e}" for e in compat['errors']))
    
    print(f"✓ Compatible (sqr={compat['sqr']}, cell_size={compat['cell_size']})")
    
    # Calculate global bounds
    print("\nCalculating bounds...")
    bounds = calculate_global_bounds(map_paths, layer)
    print(f"✓ Global: ({bounds['min_x']},{bounds['min_y']}) to ({bounds['max_x']},{bounds['max_y']})")
    print(f"  Area: {bounds['width']}×{bounds['height']} pixels")
    
    # Determine zoom levels for each map
    print(f"\nDetermining zoom levels...")
    map_levels = _calculate_map_levels(map_paths, layer, level)
    
    # Calculate canvas size at target zoom
    scale_factor = map_levels['scale_factor']
    canvas_width = int(bounds['width'] * scale_factor)
    canvas_height = int(bounds['height'] * scale_factor)
    
    print(f"  Zoom out: {map_levels['zoom_out']} levels from max {map_levels['highest_max']}")
    print(f"  Canvas: {canvas_width}×{canvas_height} pixels")
    
    # Create canvas
    output_image = Image.new('RGBA', (canvas_width, canvas_height), (0, 0, 0, 0))
    
    # Stitch each map
    print(f"\nStitching {len(map_paths)} maps...")
    for idx, map_path in enumerate(map_paths, 1):
        print(f"\n[{idx}/{len(map_paths)}] {map_path.name}")
        
        _stitch_map_onto_canvas(
            output_image=output_image,
            map_path=map_path,
            layer=layer,
            map_levels=map_levels,
            bounds=bounds,
            scale_factor=scale_factor
        )
    
    # Save
    _save_image(output_image, output_path, format)
    print(f"\n✓ Complete! Saved to {output_path}")
    print(f"  Size: {canvas_width}×{canvas_height} pixels")
    
    return output_path


def _calculate_map_levels(map_paths: List[Path], layer: int, requested_level: int) -> dict:
    """
    Calculate what pyramid level to use for each map.
    
    Key insight: Maps have different max levels, but we want consistent zoom.
    If base has 15 levels and mod has 12, then:
    - base level 15 = mod level 12 (both at max zoom)
    - base level 14 = mod level 11 (both 1 level out)
    
    Returns dict with 'highest_max', 'zoom_out', 'scale_factor', and per-map levels.
    """
    map_info = {}
    max_levels = []
    
    for map_path in map_paths:
        dzi_file = map_path / f"layer{layer}.dzi"
        dzi_info = parse_dzi(dzi_file)
        max_level = get_max_level(dzi_info['width'], dzi_info['height'])
        
        map_info[map_path] = {
            'max_level': max_level,
            'dzi_info': dzi_info
        }
        max_levels.append(max_level)
    
    highest_max = max(max_levels)
    zoom_out = highest_max - requested_level
    
    if zoom_out < 0:
        raise ValueError(f"Requested level {requested_level} > highest available {highest_max}")
    
    # Calculate actual level for each map
    for map_path, info in map_info.items():
        actual_level = max(0, info['max_level'] - zoom_out)
        info['actual_level'] = actual_level
        print(f"  {map_path.name}: level {actual_level} (max {info['max_level']})")
    
    return {
        'highest_max': highest_max,
        'zoom_out': zoom_out,
        'scale_factor': 0.5 ** zoom_out,
        'map_info': map_info
    }


def _stitch_map_onto_canvas(
    output_image: Image.Image,
    map_path: Path,
    layer: int,
    map_levels: dict,
    bounds: dict,
    scale_factor: float
):
    """
    Load tiles from one map and composite them onto the output canvas.
    
    Algorithm:
    1. Load tiles at appropriate level for this map
    2. Get world position (negate x0/y0 from map_info.json)
    3. For each tile:
       - Calculate position in full-resolution world coordinates
       - Scale to canvas coordinates
       - Paste with alpha compositing
    """
    info = map_levels['map_info'][map_path]
    actual_level = info['actual_level']
    max_level = info['max_level']
    tile_size = info['dzi_info']['tile_size']
    
    # Load tiles
    tiles = load_tiles_for_level(map_path, layer, actual_level)
    if not tiles:
        print(f"  No tiles found, skipping")
        return
    
    print(f"  Loaded {len(tiles)} tiles from level {actual_level}")
    
    # Get world position (x0/y0 are NEGATIVE world coords)
    map_info_data = read_map_info(map_path)
    world_x = -map_info_data['x0']
    world_y = -map_info_data['y0']
    
    # Scale factor to convert tile level to full resolution
    level_scale_up = 2 ** (max_level - actual_level)
    
    # Composite tiles
    pasted = 0
    for tile in tiles:
        # Calculate position in full-resolution world coordinates
        tile_full_x = world_x + (tile['x'] * tile_size * level_scale_up)
        tile_full_y = world_y + (tile['y'] * tile_size * level_scale_up)
        
        # Convert to canvas coordinates
        canvas_x = int(round((tile_full_x - bounds['min_x']) * scale_factor))
        canvas_y = int(round((tile_full_y - bounds['min_y']) * scale_factor))
        
        # Calculate expected tile size on canvas
        tile_full_w = tile['image'].size[0] * level_scale_up
        tile_full_h = tile['image'].size[1] * level_scale_up
        canvas_w = int(round(tile_full_w * scale_factor))
        canvas_h = int(round(tile_full_h * scale_factor))
        
        # Resize if needed (usually not necessary when levels align properly)
        tile_img = tile['image']
        if tile_img.size != (canvas_w, canvas_h):
            tile_img = tile_img.resize((max(1, canvas_w), max(1, canvas_h)), Image.LANCZOS)
        
        # Paste (skip if outside canvas)
        if _is_within_canvas(canvas_x, canvas_y, tile_img.size, output_image.size):
            output_image.alpha_composite(tile_img, (canvas_x, canvas_y))
            pasted += 1
    
    print(f"  Pasted {pasted} tiles")


def _is_within_canvas(x: int, y: int, tile_size: tuple, canvas_size: tuple) -> bool:
    """Check if tile position is at least partially within canvas bounds."""
    if x >= canvas_size[0] or y >= canvas_size[1]:
        return False
    if x + tile_size[0] <= 0 or y + tile_size[1] <= 0:
        return False
    return True


def _save_image(image: Image.Image, output_path: Path, format: str = None):
    """Save image with format-specific options."""
    # Auto-detect format from extension
    if format is None:
        format = output_path.suffix.upper().lstrip('.')
        if not format:
            format = 'PNG'
    
    format = format.upper()
    if format == 'JPG':
        format = 'JPEG'
    
    # Create output directory
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Format-specific handling
    save_kwargs = {}
    
    if format == 'JPEG':
        # Convert RGBA to RGB with white background
        if image.mode == 'RGBA':
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3])
            image = background
        save_kwargs = {'quality': 95, 'optimize': True}
    elif format == 'WEBP':
        save_kwargs = {'quality': 95, 'method': 6}
    elif format == 'PNG':
        save_kwargs = {'optimize': True}
    
    image.save(output_path, format=format, **save_kwargs)
