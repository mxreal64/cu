"""
Resource loading for Mu C# IDE.

Copyright (c) 2015-2026 Nicholas H.Tollervey and contributors.
"""
import os
import os.path
from mu.interface.qt import QPixmap, QIcon, QMovie, QDir

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Add search paths
QDir.addSearchPath("images", os.path.join(_BASE_DIR, "images"))
QDir.addSearchPath("css", os.path.join(_BASE_DIR, "css"))


def path(name, resource_dir="images/", ext=""):
    """Return the filename for the referenced resource."""
    return os.path.join(_BASE_DIR, resource_dir, name + ext)


def load_icon(name):
    """Load an icon from the resources directory."""
    if name.endswith(".svg") or name.endswith(".png"):
        p = path(name)
        if os.path.exists(p):
            return QIcon(p)
    svg_path = path(name, ext=".svg")
    if os.path.exists(svg_path):
        return QIcon(svg_path)
    png_path = path(name, ext=".png")
    if os.path.exists(png_path):
        return QIcon(png_path)
    return QIcon(path(name))


def load_pixmap(name, size=None):
    """Load a pixmap from the resources directory."""
    if size is not None:
        icon = load_icon(name)
        return icon.pixmap(size)
    if not (name.endswith(".png") or name.endswith(".svg") or name.endswith(".gif")):
        png_p = path(name, ext=".png")
        if os.path.exists(png_p):
            return QPixmap(png_p)
    return QPixmap(path(name))


def load_movie(name):
    """Load an animated GIF from the resources directory."""
    if not name.endswith(".gif"):
        gif_p = path(name, ext=".gif")
        if os.path.exists(gif_p):
            return QMovie(gif_p)
    return QMovie(path(name))


def load_stylesheet(name):
    """Load a CSS stylesheet from the resources directory."""
    with open(os.path.join(_BASE_DIR, "css", name), "r", encoding="utf-8") as f:
        return f.read()


def load_font_data(name):
    """Load binary content of a font."""
    with open(os.path.join(_BASE_DIR, "fonts", name), "rb") as f:
        return f.read()
