"""
Map Image Generator for pzmap2dzi Output

This package provides tools to stitch DZI tiles from pzmap2dzi output
into single map images.

Modules:
    dzi_parser: Parse DZI XML files
    map_info: Read map_info.json metadata
    pyramid: Calculate DZI pyramid levels
    discovery: Discover maps in output folders
    tile_loader: Load individual tile images
    stitcher: Stitch tiles into complete images
    bounds: Calculate global map bounds
    gui: Graphical user interface (tkinter)

Author: Kris
Version: 1.0.0
Date: 2025-11-03
"""

__version__ = "1.0.0"
__author__ = "Kris"
