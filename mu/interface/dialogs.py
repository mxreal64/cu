"""
UI dialogs for Mu C# IDE.

Copyright (c) 2015-2026 Nicholas H.Tollervey and contributors.
"""
import os
import logging
import subprocess
from mu.interface.qt import (
    QSize,
    Qt,
    QHBoxLayout,
    QVBoxLayout,
    QListWidget,
    QLabel,
    QListWidgetItem,
    QDialog,
    QDialogButtonBox,
    QPlainTextEdit,
    QTabWidget,
    QWidget,
    QCheckBox,
    QLineEdit,
    QPushButton,
    QComboBox,
    ButtonBoxOk,
    ButtonBoxCancel,
    DialogAccepted,
    NoWrap,
    exec_dialog,
)
from mu.resources import load_icon
from mu.modes.csharp import NewProjectDialog, NuGetDialog

logger = logging.getLogger(__name__)


class ModeItem(QListWidgetItem):
    """
    Represents an available mode listed for selection.
    """

    def __init__(self, name, description, icon, parent=None):
        super().__init__(parent)
        self.name = name
        self.description = description
        self.icon = icon
        text = f"{name}\n{description}"
        self.setText(text)
        self.setIcon(load_icon(self.icon))


class ModeSelector(QDialog):
    """
    Defines a UI for selecting the mode for Mu.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

    def setup(self, modes, current_mode):
        self.setMinimumSize(600, 400)
        self.setWindowTitle("Select Mode")
        widget_layout = QVBoxLayout()
        label = QLabel('Please select the desired mode then click "OK". Otherwise, click "Cancel".')
        label.setWordWrap(True)
        widget_layout.addWidget(label)
        self.setLayout(widget_layout)
        self.mode_list = QListWidget()
        self.mode_list.itemDoubleClicked.connect(self.select_and_accept)
        widget_layout.addWidget(self.mode_list)
        self.mode_list.setIconSize(QSize(48, 48))
        for name, item in modes.items():
            if not getattr(item, "is_debugger", False):
                litem = ModeItem(item.name, item.description, item.icon, self.mode_list)
                if item.icon == current_mode:
                    self.mode_list.setCurrentItem(litem)
        self.mode_list.sortItems()
        instructions = QLabel("Change mode at any time by clicking the \"Mode\" button.")
        instructions.setWordWrap(True)
        widget_layout.addWidget(instructions)
        button_box = QDialogButtonBox(ButtonBoxOk | ButtonBoxCancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        widget_layout.addWidget(button_box)

    def select_and_accept(self):
        self.accept()

    def get_mode(self):
        if self.result() == DialogAccepted and self.mode_list.currentItem():
            return self.mode_list.currentItem().icon
        else:
            raise RuntimeError("Mode change cancelled.")


class LogWidget(QWidget):
    """
    Used to display Mu's logs.
    """

    def setup(self, log):
        widget_layout = QVBoxLayout()
        self.setLayout(widget_layout)
        label = QLabel("Current Application Log:")
        label.setWordWrap(True)
        widget_layout.addWidget(label)
        self.log_text_area = QPlainTextEdit()
        self.log_text_area.setReadOnly(True)
        self.log_text_area.setLineWrapMode(NoWrap)
        self.log_text_area.setPlainText(log)
        widget_layout.addWidget(self.log_text_area)


class DotnetInfoWidget(QWidget):
    """
    Displays .NET SDK and runtime information.
    """

    def setup(self):
        layout = QVBoxLayout(self)
        label = QLabel(".NET SDK & Runtime Configuration:")
        layout.addWidget(label)
        self.text_area = QPlainTextEdit()
        self.text_area.setReadOnly(True)
        try:
            res = subprocess.run(["dotnet", "--info"], capture_output=True, text=True)
            self.text_area.setPlainText(res.stdout or res.stderr)
        except Exception as e:
            self.text_area.setPlainText(f"Error querying dotnet info: {e}")
        layout.addWidget(self.text_area)


class EnvironmentVariablesWidget(QWidget):
    """
    Used for editing and displaying environment variables for dotnet processes.
    """

    def setup(self, envars):
        widget_layout = QVBoxLayout()
        self.setLayout(widget_layout)
        label = QLabel(
            "Environment variables set when running dotnet processes.\n"
            "Each line should be in the form: NAME=VALUE"
        )
        label.setWordWrap(True)
        widget_layout.addWidget(label)
        self.text_area = QPlainTextEdit()
        self.text_area.setLineWrapMode(NoWrap)
        self.text_area.setPlainText(envars)
        widget_layout.addWidget(self.text_area)


class LocaleWidget(QWidget):
    """
    For selecting language.
    """

    def setup(self, current_locale="en"):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Interface Language:"))
        self.combo = QComboBox()
        self.combo.addItem("English (en)", "en")
        self.combo.addItem("Español (es)", "es")
        self.combo.addItem("Français (fr)", "fr")
        self.combo.addItem("Deutsch (de)", "de")
        self.combo.addItem("Italiano (it)", "it")
        self.combo.addItem("Português (pt)", "pt")
        self.combo.addItem("日本語 (ja)", "ja")
        self.combo.addItem("中文 (zh)", "zh")
        layout.addWidget(self.combo)
        layout.addStretch()

    def get_locale(self):
        return self.combo.currentData()


class AdminDialog(QDialog):
    """
    Mu Administration & Settings Dialog.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.envar_widget = None

    def setup(self, log, settings, packages, mode, device_list):
        self.setMinimumSize(600, 420)
        self.setWindowTitle("Mu C# IDE Settings")
        widget_layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        widget_layout.addWidget(self.tabs)

        self.log_widget = LogWidget(self)
        self.log_widget.setup(log)
        self.tabs.addTab(self.log_widget, "Current Log")

        self.dotnet_widget = DotnetInfoWidget(self)
        self.dotnet_widget.setup()
        self.tabs.addTab(self.dotnet_widget, ".NET SDK Info")

        self.envar_widget = EnvironmentVariablesWidget(self)
        self.envar_widget.setup(settings.get("envars", ""))
        self.tabs.addTab(self.envar_widget, "Environment Variables")

        self.locale_widget = LocaleWidget(self)
        self.locale_widget.setup(settings.get("locale", "en"))
        self.tabs.addTab(self.locale_widget, "Language")

        button_box = QDialogButtonBox(ButtonBoxOk | ButtonBoxCancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        widget_layout.addWidget(button_box)

    def settings(self):
        res = {}
        if self.envar_widget:
            res["envars"] = self.envar_widget.text_area.toPlainText()
        res["locale"] = self.locale_widget.get_locale()
        return res


class FindReplaceDialog(QDialog):
    """
    Dialog for Find and Replace.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

    def setup(self, find=None, replace=None, replace_flag=False):
        self.setMinimumSize(500, 180)
        self.setWindowTitle("Find / Replace")
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Find:"))
        self.find_term = QLineEdit(find or "")
        self.find_term.selectAll()
        layout.addWidget(self.find_term)

        layout.addWidget(QLabel("Replace (optional):"))
        self.replace_term = QLineEdit(replace or "")
        layout.addWidget(self.replace_term)

        self.replace_all_flag = QCheckBox("Replace all?")
        self.replace_all_flag.setChecked(replace_flag)
        layout.addWidget(self.replace_all_flag)

        button_box = QDialogButtonBox(ButtonBoxOk | ButtonBoxCancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def find(self):
        return self.find_term.text()

    def replace(self):
        return self.replace_term.text()

    def replace_flag(self):
        return self.replace_all_flag.isChecked()


class PackageDialog(QDialog):
    """
    Compatibility shim for package status dialog.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

    def setup(self, to_remove, to_add):
        self.setWindowTitle("Package Status")
        layout = QVBoxLayout(self)
        self.text_area = QPlainTextEdit("Packages updated.")
        self.text_area.setReadOnly(True)
        layout.addWidget(self.text_area)
        btn = QPushButton("OK")
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)
