"""
UI related capabilities for the C# code editor widget embedded in each tab in Mu.

Copyright (c) 2015-2026 Nicholas H.Tollervey and contributors.
"""
import os
import re
import logging
from mu.interface.qt import (
    Qt,
    pyqtSignal,
    QRect,
    QSize,
    QWidget,
    QPlainTextEdit,
    QApplication,
    QTextEdit,
    QColor,
    QPainter,
    QTextFormat,
    QFont,
    QSyntaxHighlighter,
    QTextCharFormat,
    QTextCursor,
    QKeySequence,
    QTextDocument,
    AlignRight,
    FindBackward,
    FindCaseSensitively,
    FindWholeWords,
)
from mu.interface.themes import Font, NightTheme, ContrastTheme, FONT_NAME, ZOOM_SIZES
from mu.logic import NEWLINE

logger = logging.getLogger(__name__)


class CSharpHighlighter(QSyntaxHighlighter):
    """
    Syntax highlighter for C# (C# 10/11/12/13/14) in Dark and High Contrast themes.
    """

    def __init__(self, document, theme_name="night"):
        super().__init__(document)
        self.theme_name = theme_name
        self.highlighting_rules = []
        self._init_styles()
        self._init_rules()

    def set_theme(self, theme_name):
        self.theme_name = theme_name if theme_name == "contrast" else "night"
        self._init_styles()
        self._init_rules()
        self.rehighlight()

    def _init_styles(self):
        is_contrast = self.theme_name == "contrast"

        def fmt(color_hex, bold=False, italic=False):
            f = QTextCharFormat()
            f.setForeground(QColor(color_hex))
            if bold:
                f.setFontWeight(QFont.Weight.Bold if hasattr(QFont, "Weight") else QFont.Bold)
            if italic:
                f.setFontItalic(True)
            return f

        if is_contrast:
            self.keyword_fmt = fmt("#FFFF00", bold=True)
            self.type_fmt = fmt("#00FFFF", bold=True)
            self.string_fmt = fmt("#FF8080")
            self.comment_fmt = fmt("#80FF80", italic=True)
            self.preprocessor_fmt = fmt("#FFA500")
            self.number_fmt = fmt("#FF00FF")
            self.attribute_fmt = fmt("#00FF80")
            self.xml_doc_fmt = fmt("#50E050", italic=True)
        else:  # Dark / Night theme
            self.keyword_fmt = fmt("#569CD6", bold=True)
            self.type_fmt = fmt("#4EC9B0")
            self.string_fmt = fmt("#D69D85")
            self.comment_fmt = fmt("#57A64A", italic=True)
            self.preprocessor_fmt = fmt("#9B9B9B")
            self.number_fmt = fmt("#B5CEA8")
            self.attribute_fmt = fmt("#DCDCAA")
            self.xml_doc_fmt = fmt("#608B4E", italic=True)

    def _init_rules(self):
        self.highlighting_rules = []

        keywords = [
            "abstract", "as", "base", "bool", "break", "byte", "case", "catch",
            "char", "checked", "class", "const", "continue", "decimal", "default",
            "delegate", "do", "double", "else", "enum", "event", "explicit",
            "extern", "false", "finally", "fixed", "float", "for", "foreach",
            "goto", "if", "implicit", "in", "int", "interface", "internal",
            "is", "lock", "long", "namespace", "new", "null", "object",
            "operator", "out", "override", "params", "private", "protected",
            "public", "readonly", "record", "ref", "return", "sbyte", "sealed",
            "short", "sizeof", "stackalloc", "static", "string", "struct",
            "switch", "this", "throw", "true", "try", "typeof", "uint", "ulong",
            "unchecked", "unsafe", "ushort", "using", "virtual", "void",
            "volatile", "while", "yield", "async", "await", "var", "dynamic",
            "when", "where", "select", "group", "by", "into", "orderby",
            "join", "let", "on", "equals", "ascending", "descending",
            "init", "file", "required", "scoped", "with"
        ]
        for kw in keywords:
            pattern = rf"\b{kw}\b"
            self.highlighting_rules.append((re.compile(pattern), self.keyword_fmt))

        types = [
            r"\b[A-Z][a-zA-Z0-9_]*(?:<[a-zA-Z0-9_, <>\?]+>)?\b",
            r"\b(Task|ValueTask|Action|Func|List|Dictionary|IEnumerable|ICollection|IList|IDictionary|Span|ReadOnlySpan|Memory|String|Int32|Int64|Boolean|Guid|DateTime|TimeSpan|Console|Math)\b"
        ]
        for t in types:
            self.highlighting_rules.append((re.compile(t), self.type_fmt))

        num_pattern = r"\b(?:0[xX][0-9a-fA-F_]+|0[bB][01_]+|[0-9][0-9_]*(?:\.[0-9_]+)?(?:[eE][+-]?[0-9_]+)?[fFdDmMuUlL]?)\b"
        self.highlighting_rules.append((re.compile(num_pattern), self.number_fmt))

        self.highlighting_rules.append((re.compile(r"^\s*#\s*(?:if|else|elif|endif|define|undef|warning|error|line|region|endregion|pragma|nullable)\b.*"), self.preprocessor_fmt))
        self.highlighting_rules.append((re.compile(r"\[\s*[A-Z][a-zA-Z0-9_]*(?:\(.*?\))?\s*\]"), self.attribute_fmt))

        self.highlighting_rules.append((re.compile(r'"[^"\\]*(?:\\.[^"\\]*)*"'), self.string_fmt))
        self.highlighting_rules.append((re.compile(r'\$@"[^"]*"'), self.string_fmt))
        self.highlighting_rules.append((re.compile(r'@"[^"]*"'), self.string_fmt))
        self.highlighting_rules.append((re.compile(r"\$'[^']*'"), self.string_fmt))
        self.highlighting_rules.append((re.compile(r"'[^'\\]*(?:\\.[^'\\]*)*'"), self.string_fmt))

        self.highlighting_rules.append((re.compile(r"///[^\n]*"), self.xml_doc_fmt))
        self.highlighting_rules.append((re.compile(r"//[^\n]*"), self.comment_fmt))

    def highlightBlock(self, text):
        for pattern, fmt in self.highlighting_rules:
            for match in pattern.finditer(text):
                start, end = match.span()
                self.setFormat(start, end - start, fmt)

        self.setCurrentBlockState(0)
        start_index = 0
        if self.previousBlockState() != 1:
            start_index = text.find("/*")

        while start_index >= 0:
            end_index = text.find("*/", start_index + 2)
            if end_index == -1:
                self.setCurrentBlockState(1)
                comment_len = len(text) - start_index
            else:
                comment_len = end_index - start_index + 2
            self.setFormat(start_index, comment_len, self.comment_fmt)
            start_index = text.find("/*", start_index + comment_len)


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.editor.line_number_area_paint_event(event)


class EditorPane(QPlainTextEdit):
    open_file = pyqtSignal(str)
    context_menu = pyqtSignal()

    def __init__(self, path, text, newline=NEWLINE):
        super().__init__()
        self.path = path
        self.newline = newline
        self.theme_name = "night"
        self.has_annotations = False
        self.check_indicators = {"error": {}, "style": {}}

        font = QFont(FONT_NAME)
        font.setPointSize(14)
        font.setStyleHint(QFont.StyleHint.Monospace if hasattr(QFont, "StyleHint") else QFont.Monospace)
        self.setFont(font)
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(" ") * 4)

        self.line_number_area = LineNumberArea(self)
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.update_line_number_area_width(0)

        self.highlighter = CSharpHighlighter(self.document(), self.theme_name)

        if text:
            self.setPlainText(text)

        self.set_theme(self.theme_name)

    def line_number_area_width(self):
        digits = 1
        max_num = max(1, self.blockCount())
        while max_num >= 10:
            max_num //= 10
            digits += 1
        return 24 + self.fontMetrics().horizontalAdvance("9") * digits

    def update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(
            QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height())
        )

    def highlight_current_line(self):
        extra_selections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = QColor("#2A2D2E")
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection if hasattr(QTextFormat, "Property") else QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)

        for line_num, err_text in self.check_indicators.get("error", {}).items():
            block = self.document().findBlockByNumber(line_num - 1)
            if block.isValid():
                sel = QTextEdit.ExtraSelection()
                sel.format.setUnderlineColor(QColor("#E51400"))
                sel.format.setUnderlineStyle(QTextCharFormat.UnderlineStyle.WaveUnderline if hasattr(QTextCharFormat, "UnderlineStyle") else QTextCharFormat.WaveUnderline)
                cursor = QTextCursor(block)
                cursor.select(QTextCursor.SelectionType.LineUnderCursor if hasattr(QTextCursor, "SelectionType") else QTextCursor.LineUnderCursor)
                sel.cursor = cursor
                extra_selections.append(sel)

        self.setExtraSelections(extra_selections)

    def line_number_area_paint_event(self, event):
        painter = QPainter(self.line_number_area)
        if self.theme_name == "contrast":
            bg_color = QColor("#000000")
            fg_color = QColor("#FFFFFF")
        else:  # Dark / Night theme
            bg_color = QColor("#1E1E1E")
            fg_color = QColor("#6E7681")

        painter.fillRect(event.rect(), bg_color)

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        current_line = self.textCursor().blockNumber()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                font = painter.font()
                if block_number == current_line:
                    painter.setPen(QColor("#569CD6"))
                    font.setBold(True)
                else:
                    painter.setPen(fg_color)
                    font.setBold(False)
                painter.setFont(font)

                painter.drawText(
                    0,
                    top,
                    self.line_number_area.width() - 8,
                    self.fontMetrics().height(),
                    AlignRight,
                    number,
                )

                if (block_number + 1) in self.check_indicators.get("error", {}):
                    painter.setBrush(QColor("#E51400"))
                    painter.setPen(Qt.PenStyle.NoPen if hasattr(Qt, "PenStyle") else Qt.NoPen)
                    painter.drawEllipse(4, top + 4, 8, 8)

            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1

    def set_theme(self, theme_name):
        if hasattr(theme_name, "name"):
            theme_name = theme_name.name.lower()
        elif not isinstance(theme_name, str):
            theme_name = "night"
        theme_name = "contrast" if theme_name == "contrast" else "night"
        self.theme_name = theme_name
        self.highlighter.set_theme(theme_name)
        if theme_name == "contrast":
            self.setStyleSheet("background-color: #000000; color: #FFFFFF; border: none;")
        else:
            self.setStyleSheet("background-color: #1E1E1E; color: #D4D4D4; border: none;")
        self.highlight_current_line()
        self.line_number_area.update()

    def set_zoom(self, zoom_size):
        pt = ZOOM_SIZES.get(zoom_size, 14)
        font = self.font()
        font.setPointSize(pt)
        self.setFont(font)
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(" ") * 4)
        self.update_line_number_area_width(0)

    def text(self):
        return self.toPlainText()

    def setText(self, text):
        self.setPlainText(text)

    def lines(self):
        return self.blockCount()

    def lineLength(self, line_num):
        block = self.document().findBlockByNumber(line_num)
        return len(block.text()) if block.isValid() else 0

    def getSelection(self):
        cursor = self.textCursor()
        if not cursor.hasSelection():
            pos = cursor.position()
            block = cursor.block()
            line = block.blockNumber()
            col = pos - block.position()
            return line, col, line, col
        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        start_block = self.document().findBlock(start)
        end_block = self.document().findBlock(end)
        return (
            start_block.blockNumber(),
            start - start_block.position(),
            end_block.blockNumber(),
            end - end_block.position(),
        )

    def setSelection(self, start_line, start_col, end_line, end_col):
        start_block = self.document().findBlockByNumber(start_line)
        end_block = self.document().findBlockByNumber(end_line)
        if not (start_block.isValid() and end_block.isValid()):
            return
        cursor = self.textCursor()
        cursor.setPosition(start_block.position() + start_col)
        cursor.setPosition(end_block.position() + end_col, QTextCursor.MoveMode.KeepAnchor if hasattr(QTextCursor, "MoveMode") else QTextCursor.KeepAnchor)
        self.setTextCursor(cursor)

    def setCursorPosition(self, line, col):
        block = self.document().findBlockByNumber(line)
        if block.isValid():
            cursor = self.textCursor()
            pos = min(block.position() + col, block.position() + len(block.text()))
            cursor.setPosition(pos)
            self.setTextCursor(cursor)
            self.ensureCursorVisible()

    def getCursorPosition(self):
        cursor = self.textCursor()
        block = cursor.block()
        return block.blockNumber(), cursor.position() - block.position()

    def ensureLineVisible(self, line):
        self.setCursorPosition(line, 0)
        self.ensureCursorVisible()

    def clear_annotations(self):
        self.check_indicators = {"error": {}, "style": {}}
        self.has_annotations = False
        self.highlight_current_line()
        self.line_number_area.update()

    def annotate(self, line, message, category="error"):
        if category not in self.check_indicators:
            self.check_indicators[category] = {}
        self.check_indicators[category][line] = message
        self.has_annotations = True
        self.highlight_current_line()
        self.line_number_area.update()

    @property
    def label(self):
        name = os.path.basename(self.path) if self.path else "untitled"
        if self.document().isModified():
            name += " *"
        return name

    @property
    def title(self):
        name = self.path if self.path else "untitled"
        if self.document().isModified():
            name += " (*)"
        return name

    def isModified(self):
        return self.document().isModified()

    def setModified(self, mod):
        self.document().setModified(mod)

    def connect_margin(self, handler):
        pass

    def set_api(self, api):
        pass

    def reset_annotations(self):
        self.clear_annotations()

    def annotate_code(self, feedback, annotation_type="error"):
        for item in feedback:
            line = item.get("line") or (item.get("line_no", 0) + 1)
            msg = item.get("message", "")
            self.annotate(line, msg, annotation_type)

    def show_annotations(self):
        self.highlight_current_line()
        self.line_number_area.update()

    def toggle_comments(self):
        cursor = self.textCursor()
        if not cursor.hasSelection():
            cursor.select(QTextCursor.SelectionType.LineUnderCursor if hasattr(QTextCursor, "SelectionType") else QTextCursor.LineUnderCursor)
        selected_text = cursor.selectedText()
        lines = selected_text.split("\u2029")
        all_commented = all(l.strip().startswith("//") for l in lines if l.strip())
        new_lines = []
        for l in lines:
            if all_commented:
                if l.lstrip().startswith("// "):
                    new_lines.append(l.replace("// ", "", 1))
                elif l.lstrip().startswith("//"):
                    new_lines.append(l.replace("//", "", 1))
                else:
                    new_lines.append(l)
            else:
                new_lines.append("// " + l if l.strip() else l)
        cursor.insertText("\n".join(new_lines))

    def findFirst(self, text, regex=False, cs=False, wo=False, wrap=True, forward=True, line=-1, index=-1, show=True, posix=False):
        flags = QTextDocument.FindFlag(0) if hasattr(QTextDocument, "FindFlag") else QTextDocument.FindFlags()
        if not forward:
            flags |= FindBackward
        if cs:
            flags |= FindCaseSensitively
        if wo:
            flags |= FindWholeWords
        cursor = self.textCursor()
        if line >= 0 and index >= 0:
            self.setCursorPosition(line, index)
            cursor = self.textCursor()
        found_cursor = self.document().find(text, cursor, flags)
        if not found_cursor.isNull():
            self.setTextCursor(found_cursor)
            return True
        if wrap:
            start_cursor = QTextCursor(self.document())
            if not forward:
                start_cursor.movePosition(QTextCursor.MoveOperation.End if hasattr(QTextCursor, "MoveOperation") else QTextCursor.End)
            found_cursor = self.document().find(text, start_cursor, flags)
            if not found_cursor.isNull():
                self.setTextCursor(found_cursor)
                return True
        return False

    def findNext(self):
        return False

    def replace(self, replacement):
        cursor = self.textCursor()
        if cursor.hasSelection():
            cursor.insertText(replacement)

    def SendScintilla(self, *args):
        pass

    def keyPressEvent(self, event):
        key_return = Qt.Key.Key_Return if hasattr(Qt, "Key") else Qt.Key_Return
        key_enter = Qt.Key.Key_Enter if hasattr(Qt, "Key") else Qt.Key_Enter
        key_tab = Qt.Key.Key_Tab if hasattr(Qt, "Key") else Qt.Key_Tab

        if event.key() in (key_return, key_enter):
            cursor = self.textCursor()
            block_text = cursor.block().text()
            indent = ""
            for ch in block_text:
                if ch in (" ", "\t"):
                    indent += ch
                else:
                    break
            if block_text.rstrip().endswith("{"):
                indent += "    "
            super().keyPressEvent(event)
            self.insertPlainText(indent)
            return
        elif event.key() == key_tab:
            self.insertPlainText("    ")
            return
        super().keyPressEvent(event)
