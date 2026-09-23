"""
Contains the base class for Mu editor modes.

Copyright (c) 2015-2026 Nicholas H.Tollervey and contributors.
"""
import os
import os.path
import logging
from mu.interface.qt import QObject
from .. import config, settings

logger = logging.getLogger(__name__)


class BaseMode(QObject):
    """
    Represents the common aspects of a mode.
    """

    name = "UNNAMED MODE"
    short_name = "UNDEFINED_MODE"
    description = "DESCRIPTION NOT AVAILABLE."
    icon = "help"
    repl = False
    plotter = False
    is_debugger = False
    has_debugger = False
    save_timeout = 5
    builtins = None
    file_extensions = [".cs", ".csproj", ".sln", ".json"]
    module_names = set()
    code_template = """// Write your C# code here :-)
using System;

Console.WriteLine("Hello, C# World!");
"""

    def __init__(self, editor, view):
        self.editor = editor
        self.view = view
        super().__init__()

    def stop(self):
        """
        Called if/when the editor quits when in this mode.
        """
        pass

    def actions(self):
        """
        Return an ordered list of actions provided by this module.
        """
        return []

    @staticmethod
    def workspace_dir():
        """
        Return the location on the filesystem for opening and closing files.
        """
        workspace_dir = os.path.join(
            config.HOME_DIRECTORY, config.WORKSPACE_NAME
        )
        settings_workspace = settings.settings.get("workspace")

        if settings_workspace:
            if os.path.isdir(settings_workspace):
                workspace_dir = settings_workspace
            else:
                logger.warning(
                    f"Workspace {settings_workspace} not valid; using {workspace_dir}"
                )

        os.makedirs(workspace_dir, exist_ok=True)
        return workspace_dir

    def api(self):
        return []

    def set_buttons(self, **kwargs):
        for k, v in kwargs.items():
            if k in self.view.button_bar.slots:
                self.view.button_bar.slots[k].setEnabled(bool(v))

    def return_focus_to_current_tab(self):
        if self.view.current_tab:
            self.view.current_tab.setFocus()

    def open_file(self, path):
        return None, None

    def activate(self):
        pass

    def ensure_state(self):
        pass

    def deactivate(self):
        pass

    def device_changed(self, new_device):
        pass
