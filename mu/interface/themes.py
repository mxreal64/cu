"""
Theme and presentation related code for Mu C# IDE.

Copyright (c) 2015-2026 Nicholas H.Tollervey and contributors.
"""
import logging
from mu.interface.qt import QColor, QFontDatabase
from mu.resources import load_stylesheet, load_font_data

# The default font size.
DEFAULT_FONT_SIZE = 14
FONT_NAME = "Source Code Pro"

FONT_FILENAME_PATTERN = "SourceCodePro-{variant}.otf"
FONT_VARIANTS = ("Bold", "BoldIt", "It", "Regular", "Semibold", "SemiboldIt")

# Dark Theme is the only and default base theme (light mode ripped out)
NIGHT_STYLE = load_stylesheet("night.css")
DAY_STYLE = NIGHT_STYLE  # Light mode replaced with Dark Theme
CONTRAST_STYLE = load_stylesheet("contrast.css")

MIN_WINDOW_WIDTH = 600
MIN_WINDOW_HEIGHT = 400

ZOOM_SIZES = {
    "xs": 8,
    "s": 10,
    "m": 14,
    "l": 16,
    "xl": 18,
    "xxl": 24,
    "xxxl": 28,
}

logger = logging.getLogger(__name__)


class Font:
    """
    Utility class for font settings.
    """

    _DATABASE = None

    def __init__(self, color="#D4D4D4", paper="#1E1E1E", bold=False, italic=False):
        self.color = color
        self.paper = paper
        self.bold = bold
        self.italic = italic

    @classmethod
    def get_database(cls):
        if cls._DATABASE is None:
            cls._DATABASE = QFontDatabase()
            for variant in FONT_VARIANTS:
                filename = FONT_FILENAME_PATTERN.format(variant=variant)
                font_data = load_font_data(filename)
                cls._DATABASE.addApplicationFontFromData(font_data)
        return cls._DATABASE

    def load(self, size=DEFAULT_FONT_SIZE):
        return Font.get_database().font(FONT_NAME, self.stylename, size)

    @property
    def stylename(self):
        if self.bold:
            if self.italic:
                return "Semibold Italic"
            return "Semibold"
        if self.italic:
            return "Italic"
        return "Regular"


class Theme:
    """
    Base Theme definition for Dark IDE.
    """
    name = "night"
    FunctionMethodName = ClassName = Font(color="#4EC9B0", paper="#1E1E1E")
    UnclosedString = Font(paper="#C93827")
    Comment = CommentBlock = CommentLine = Font(color="#57A64A", italic=True, paper="#1E1E1E")
    Keyword = Font(color="#569CD6", bold=True, paper="#1E1E1E")
    SingleQuotedString = DoubleQuotedString = Font(color="#D69D85", paper="#1E1E1E")
    Number = Font(color="#B5CEA8", paper="#1E1E1E")
    Decorator = Font(color="#DCDCAA", paper="#1E1E1E")
    Default = Identifier = Font(color="#D4D4D4", paper="#1E1E1E")
    Operator = Font(color="#D4D4D4", paper="#1E1E1E")
    HighlightedIdentifier = Font(color="#9CDCFE", paper="#1E1E1E")
    Paper = QColor("#1E1E1E")
    Caret = QColor("#C6C6C6")
    Margin = QColor("#252526")
    IndicatorError = QColor("#F14C4C")
    IndicatorStyle = QColor("#3794FF")
    DebugStyle = QColor("#444")
    IndicatorWordMatch = QColor("#616161")
    BraceBackground = QColor("#0E639C")
    BraceForeground = QColor("#FFFFFF")
    UnmatchedBraceBackground = QColor("#F14C4C")
    UnmatchedBraceForeground = QColor("#FFFFFF")
    BreakpointMarker = QColor("#E51400")


class NightTheme(Theme):
    name = "night"


# Light mode is mapped to Dark / Night theme
DayTheme = NightTheme


class ContrastTheme(Theme):
    name = "contrast"
    FunctionMethodName = ClassName = Font(color="#00FFFF", bold=True, paper="#000000")
    UnclosedString = Font(paper="#666666")
    Comment = CommentBlock = Font(color="#80FF80", italic=True, paper="#000000")
    Keyword = Font(color="#FFFF00", bold=True, paper="#000000")
    SingleQuotedString = DoubleQuotedString = Font(color="#FF8080", paper="#000000")
    Number = Font(color="#FF00FF", paper="#000000")
    Decorator = Font(color="#00FF80", paper="#000000")
    Default = Identifier = Font(color="#FFFFFF", paper="#000000")
    Operator = Font(color="#FFFFFF", paper="#000000")
    HighlightedIdentifier = Font(color="#FFFF00", paper="#000000")
    Paper = QColor("#000000")
    Caret = QColor("#FFFFFF")
    Margin = QColor("#111111")
    IndicatorError = QColor("#FF0000")
    IndicatorStyle = QColor("#00FFFF")
    DebugStyle = QColor("#666666")
    IndicatorWordMatch = QColor("#888888")
    BraceBackground = QColor("#FFFFFF")
    BraceForeground = QColor("#000000")
    UnmatchedBraceBackground = QColor("#FF0000")
    UnmatchedBraceForeground = QColor("#FFFFFF")
    BreakpointMarker = QColor("#FF0000")
