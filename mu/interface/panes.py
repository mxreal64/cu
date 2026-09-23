"""
Contains the UI classes used for process running, terminal output, and tools in Mu C# IDE.

Copyright (c) 2015-2026 Nicholas H.Tollervey and contributors.
"""
import sys
import os
import re
import platform
import logging
import signal
import string
from collections import deque
from mu.interface.qt import (
    Qt,
    QProcess,
    QProcessEnvironment,
    pyqtSignal,
    QTimer,
    QUrl,
    QMessageBox,
    QTextEdit,
    QFrame,
    QListWidget,
    QGridLayout,
    QLabel,
    QMenu,
    QTreeView,
    QKeySequence,
    QTextCursor,
    QCursor,
    QPainter,
    QDesktopServices,
    QStandardItem,
    QFont,
    SelectRows,
)
from mu.interface.themes import Font, DEFAULT_FONT_SIZE

logger = logging.getLogger(__name__)

PANE_ZOOM_SIZES = {
    "xs": 8,
    "s": 10,
    "m": 14,
    "l": 16,
    "xl": 18,
    "xxl": 24,
    "xxxl": 28,
}


class ProcessPane(QTextEdit):
    """
    Interactive process runner & console pane for dotnet / C# execution.
    """

    on_append_text = pyqtSignal(bytes)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.process = None
        self.running = False
        self.reading_stdout = False
        self.stdout_buffer = b""
        self.start_of_current_line = 0
        self.input_history = []
        self.history_position = 0
        self.font_size = DEFAULT_FONT_SIZE
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.context_menu)

        from mu.interface.themes import FONT_NAME
        font = self.font()
        font.setFamily(FONT_NAME)
        font.setPointSize(self.font_size)
        font.setStyleHint(QFont.Monospace)
        self.setFont(font)

    def start_process(
        self,
        interpreter,
        script_name=None,
        working_directory=None,
        interactive=False,
        debugger=False,
        command_args=None,
        envars=None,
        python_args=None,
    ):
        if isinstance(interpreter, (list, tuple)):
            cmd = interpreter[0]
            args = list(interpreter[1:])
            if script_name:
                args.append(script_name)
            if command_args:
                args.extend(command_args)
        else:
            cmd = interpreter
            args = []
            if script_name:
                args.append(script_name)
            if command_args:
                args.extend(command_args)

        if not working_directory:
            working_directory = os.getcwd()

        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        env = QProcessEnvironment.systemEnvironment()
        env.insert("DOTNET_CLI_TELEMETRY_OPTOUT", "1")
        if envars:
            for k, v in envars.items():
                env.insert(k, v)

        self.process.setWorkingDirectory(working_directory)
        self.process.setProcessEnvironment(env)
        self.process.readyRead.connect(self.try_read_from_stdout)
        self.process.finished.connect(self.finished)

        logger.info(f"Starting process: {cmd} {args} in {working_directory}")
        self.process.start(cmd, args)
        self.running = True

    def stop_process(self):
        if self.process:
            self.process.terminate()
            if not self.process.waitForFinished(1000):
                self.process.kill()
                self.process.waitForFinished()
            self.running = False

    def finished(self, code, status):
        self.running = False
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(f"\n\n---------- PROCESS FINISHED (Exit code: {code}) ----------\n")
        self.setTextCursor(cursor)
        self.setReadOnly(True)

    def try_read_from_stdout(self):
        if not self.reading_stdout:
            self.reading_stdout = True
            self.read_from_stdout()

    def read_from_stdout(self):
        if not self.process:
            self.reading_stdout = False
            return
        data = self.process.read(1024)
        if data:
            data = self.stdout_buffer + data
            try:
                self.append_text(data)
                self.on_append_text.emit(data)
                self.set_start_of_current_line()
                self.stdout_buffer = b""
            except UnicodeDecodeError:
                self.stdout_buffer = data
            QTimer.singleShot(2, self.read_from_stdout)
        else:
            self.reading_stdout = False

    def append_text(self, msg_bytes):
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(msg_bytes.decode("utf-8", errors="replace"))
        cursor.movePosition(QTextCursor.End)
        self.setTextCursor(cursor)
        self.ensureCursorVisible()

    def write_to_stdin(self, data):
        if self.process and self.running:
            self.process.write(data)

    def set_start_of_current_line(self):
        self.start_of_current_line = len(self.toPlainText())

    def parse_input(self, key, text, modifiers):
        msg = b""
        if key in (Qt.Key_Enter, Qt.Key_Return):
            msg = b"\n"
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.End)
            self.setTextCursor(cursor)
            cursor.insertText("\n")
            content = self.toPlainText()
            line = content[self.start_of_current_line :].encode("utf-8")
            self.write_to_stdin(line)
            if line.strip():
                self.input_history.append(line.replace(b"\n", b""))
            self.history_position = 0
            self.set_start_of_current_line()
            return
        elif (modifiers == Qt.ControlModifier and key == Qt.Key_C):
            if self.process and self.running:
                self.stop_process()
                return
        elif text and text.isprintable():
            msg = text.encode("utf-8")
            cursor = self.textCursor()
            if cursor.position() < self.start_of_current_line:
                cursor.movePosition(QTextCursor.End)
            cursor.insertText(text)
            self.setTextCursor(cursor)
            self.write_to_stdin(msg)

    def keyPressEvent(self, event):
        self.parse_input(event.key(), event.text(), event.modifiers())

    def context_menu(self):
        menu = QMenu(self)
        menu.addAction("Copy", self.copy)
        menu.addAction("Paste", self.paste)
        menu.addAction("Clear", self.clear)
        menu.exec_(QCursor.pos())

    def set_font_size(self, new_size=DEFAULT_FONT_SIZE):
        self.font_size = new_size
        f = self.font()
        f.setPointSize(new_size)
        self.setFont(f)

    def set_zoom(self, size):
        self.set_font_size(PANE_ZOOM_SIZES.get(size, 14))

    def set_theme(self, theme):
        if theme == "night":
            self.setStyleSheet("background-color: #1E1E1E; color: #D4D4D4; border: none;")
        elif theme == "contrast":
            self.setStyleSheet("background-color: #000000; color: #FFFFFF; border: none;")
        else:
            self.setStyleSheet("background-color: #FFFFFF; color: #000000; border: none;")


# Backward compatibility aliases
PythonProcessPane = ProcessPane
JupyterREPLPane = ProcessPane
MicroPythonREPLPane = ProcessPane
SnekREPLPane = ProcessPane


class DebugInspectorItem(QStandardItem):
    def __init__(self, *args):
        super().__init__(*args)
        self.setEditable(False)


class DebugInspector(QTreeView):
    def __init__(self):
        super().__init__()
        self.setUniformRowHeights(True)

    def set_zoom(self, size):
        pass

    def set_theme(self, theme):
        pass


class FileSystemPane(QFrame):
    def __init__(self, home, parent=None):
        super().__init__(parent)

    def set_zoom(self, size):
        pass

    def set_theme(self, theme):
        pass


class PlotterPane(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.raw_data = []

    def set_zoom(self, size):
        pass

    def set_theme(self, theme):
        pass
