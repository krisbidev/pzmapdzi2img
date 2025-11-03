"""
Map Discovery

Discovers all available maps in pzmap2dzi output folder and analyzes their properties.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Union
import logging

from .map_info import read_map_info
from .dzi_parser import parse_dzi

logger = logging.getLogger(__name__)


def discover_maps(data_folder: Union[str, Path]) -> Dict[str, Dict[str, Any]]:
    """
    Discover all available maps in pzmap2dzi output folder.
    
    Searches for:
    - Base map: base_top/
    - Overlay maps: foraging_top/, zombie_top/, streets_top/
    - Mod maps: mod_maps/*/base_top/
    
    Args:
        data_folder: Path to pzmap2dzi output folder (typically out/html/map_data/)
        
    Returns:
        Dictionary of {map_name: map_metadata}
        
    Raises:
        FileNotFoundError: If data_folder doesn't exist
        ValueError: If no maps found in folder
        
    Example:
        >>> maps = discover_maps('out/html/map_data')
        >>> print(maps.keys())
        dict_keys(['base', 'foraging', 'zombie', 'Old Mill', ...])
        >>> print(maps['base']['layers'])
        [0, 1, 2, 3, 4, 5, 6, 7]
    """
    data_folder = Path(data_folder)
    
    if not data_folder.exists():
        raise FileNotFoundError(
            f"Data folder not found: {data_folder}\n"
            f"Expected pzmap2dzi output folder (typically out/html/map_data/)"
        )
    
    maps = {}
    
    # Find base map
    base_path = data_folder / "base_top"
    if base_path.exists():
        try:
            maps["base"] = analyze_map(base_path)
            logger.info(f"Found base map: {base_path}")
        except Exception as e:
            logger.warning(f"Failed to analyze base map: {e}")
    
    # Find overlay maps (foraging, zombie, streets)
    for overlay_name in ["foraging_top", "zombie_top", "streets_top"]:
        overlay_path = data_folder / overlay_name
        if overlay_path.exists():
            try:
                # Remove "_top" suffix for cleaner name
                clean_name = overlay_name.replace("_top", "")
                maps[clean_name] = analyze_map(overlay_path)
                logger.info(f"Found overlay map: {overlay_name}")
            except Exception as e:
                logger.warning(f"Failed to analyze {overlay_name}: {e}")
    
    # Find mod maps
    mod_folder = data_folder / "mod_maps"
    if mod_folder.exists() and mod_folder.is_dir():
        for mod_dir in mod_folder.iterdir():
            if mod_dir.is_dir():
                mod_base = mod_dir / "base_top"
                if mod_base.exists():
                    try:
                        maps[mod_dir.name] = analyze_map(mod_base)
                        logger.info(f"Found mod map: {mod_dir.name}")
                    except Exception as e:
                        logger.warning(f"Failed to analyze mod {mod_dir.name}: {e}")
    
    if not maps:
        raise ValueError(
            f"No maps found in {data_folder}\n"
            f"Expected to find base_top/ or mod_maps/*/ directories\n"
            f"Make sure pzmap2dzi has been run successfully"
        )
    
    logger.info(f"Discovered {len(maps)} maps total")
    return maps


def analyze_map(map_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Analyze a single map and extract all its properties.
    
    Args:
        map_path: Path to map folder (e.g., base_top/ or mod_maps/SomeMap/base_top/)
        
    Returns:
        Dictionary with keys:
            - path: Path to map folder
            - name: Map name (folder name)
            - map_info: Full map_info.json contents
            - layers: List of available layer numbers [0, 1, 2, ...]
            - levels: List of available zoom level numbers [0, 1, 2, ...]
            - min_level: Lowest available level
            - max_level: Highest available level
            - tile_size: DZI tile size (typically 300)
            - format: Image format (webp, png, jpg)
            - width: Full width in pixels
            - height: Full height in pixels
            - x0: Origin X coordinate
            - y0: Origin Y coordinate
            - skip: Number of top levels omitted
            - sqr: Square size multiplier
            
    Raises:
        FileNotFoundError: If map_path doesn't exist
        ValueError: If required files missing
        
    Example:
        >>> info = analyze_map('out/html/map_data/base_top')
        >>> print(info['layers'])
        [0, 1, 2, 3, 4, 5, 6, 7]
        >>> print(info['max_level'])
        15
    """
    map_path = Path(map_path)
    
    if not map_path.exists():
        raise FileNotFoundError(f"Map path not found: {map_path}")
    
    # Read map_info.json
    map_info = read_map_info(map_path)
    
    # Detect available layers by finding .dzi files
    layers = []
    for item in map_path.iterdir():
        if item.is_file() and item.name.startswith("layer") and item.name.endswith(".dzi"):
            try:
                # Extract number from "layerN.dzi"
                layer_num = int(item.stem[5:])  # "layer0" -> 0
                layers.append(layer_num)
            except (ValueError, IndexError):
                logger.warning(f"Could not parse layer number from: {item.name}")
    
    if not layers:
        raise ValueError(
            f"No layer files found in {map_path}\n"
            f"Expected to find layer0.dzi, layer1.dzi, etc."
        )
    
    layers.sort()
    
    # Detect actual zoom levels by checking directory structure
    # Use first layer as reference (all layers should have same levels)
    layer_folder = map_path / f"layer{layers[0]}_files"
    levels = []
    
    if layer_folder.exists():
        for item in layer_folder.iterdir():
            if item.is_dir() and item.name.isdigit():
                levels.append(int(item.name))
    
    if not levels:
        raise ValueError(
            f"No level directories found in {layer_folder}\n"
            f"Expected to find 0/, 1/, 2/, etc."
        )
    
    levels.sort()
    
    # Parse first .dzi file for tile size and format
    dzi_path = map_path / f"layer{layers[0]}.dzi"
    dzi_info = parse_dzi(dzi_path)
    
    # Verify consistency with map_info.json
    if dzi_info['width'] != map_info['w'] or dzi_info['height'] != map_info['h']:
        logger.warning(
            f"Dimension mismatch in {map_path.name}:\n"
            f"  map_info.json: {map_info['w']}×{map_info['h']}\n"
            f"  {dzi_path.name}: {dzi_info['width']}×{dzi_info['height']}"
        )
    
    return {
        'path': map_path,
        'name': map_path.name,
        'map_info': map_info,
        'layers': layers,
        'levels': levels,
        'min_level': min(levels),
        'max_level': max(levels),
        'tile_size': dzi_info['tile_size'],
        'format': dzi_info['format'],
        'width': map_info['w'],
        'height': map_info['h'],
        'x0': map_info['x0'],
        'y0': map_info['y0'],
        'skip': map_info.get('skip', 0),
        'sqr': map_info['sqr'],
        'cell_size': map_info['cell_size']
    }


def get_map_summary(maps: Dict[str, Dict[str, Any]]) -> str:
    """
    Generate a human-readable summary of discovered maps.
    
    Args:
        maps: Dictionary from discover_maps()
        
    Returns:
        Formatted string summarizing all maps
        
    Example:
        >>> maps = discover_maps('out/html/map_data')
        >>> print(get_map_summary(maps))
        Found 3 maps:
          base: 19800×15900 px, 8 layers, levels 0-15
          Old Mill: 300×1200 px, 8 layers, levels 0-11
          ...
    """
    lines = [f"Found {len(maps)} map{'s' if len(maps) != 1 else ''}:"]
    
    for name, info in sorted(maps.items()):
        dims = f"{info['width']}×{info['height']} px"
        layer_count = len(info['layers'])
        level_range = f"{info['min_level']}-{info['max_level']}"
        
        line = f"  {name}: {dims}, {layer_count} layers, levels {level_range}"
        
        # Add notes for non-standard configs
        notes = []
        if info['skip'] > 0:
            notes.append(f"skip={info['skip']}")
        if info['sqr'] != 1:
            notes.append(f"sqr={info['sqr']}")
        
        if notes:
            line += f" ({', '.join(notes)})"
        
        lines.append(line)
    
    return '\n'.join(lines)


def filter_maps(
    maps: Dict[str, Dict[str, Any]],
    include_base: bool = True,
    include_overlays: bool = False,
    include_mods: bool = True,
    mod_names: List[str] = None
) -> Dict[str, Dict[str, Any]]:
    """
    Filter discovered maps based on type and names.
    
    Args:
        maps: Dictionary from discover_maps()
        include_base: Include base map
        include_overlays: Include foraging/zombie/streets overlays
        include_mods: Include all mod maps
        mod_names: Specific mod names to include (overrides include_mods if provided)
        
    Returns:
        Filtered dictionary of maps
        
    Example:
        >>> all_maps = discover_maps('out/html/map_data')
        >>> base_only = filter_maps(all_maps, include_base=True, include_mods=False)
        >>> print(base_only.keys())
        dict_keys(['base'])
    """
    filtered = {}
    
    overlay_names = ['foraging', 'zombie', 'streets']
    
    for name, info in maps.items():
        # Base map
        if name == 'base' and include_base:
            filtered[name] = info
        # Overlay maps
        elif name in overlay_names and include_overlays:
            filtered[name] = info
        # Mod maps
        elif name not in ['base'] + overlay_names:
            if mod_names is not None:
                # Specific mod list provided
                if name in mod_names:
                    filtered[name] = info
            elif include_mods:
                # Include all mods
                filtered[name] = info
    
    return filtered

