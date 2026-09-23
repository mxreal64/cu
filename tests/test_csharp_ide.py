"""
Comprehensive test suite for Mu C# IDE.
"""
import os
import unittest
from unittest.mock import MagicMock, patch

from mu.interface.qt import QApplication
from mu.logic import Editor
from mu.interface.main import Window
from mu.app import setup_modes
from mu.modes import CSharpMode, CSharpWebMode, CSharpTestMode, CSharpReplMode
from mu.interface.editor import EditorPane, CSharpHighlighter
from mu.interface.panes import ProcessPane
from mu.interface.dialogs import ModeSelector, AdminDialog, NewProjectDialog, NuGetDialog

app = QApplication.instance() or QApplication([])


class TestMuCSharpIDE(unittest.TestCase):
    def setUp(self):
        self.win = Window()
        self.editor = Editor(view=self.win)
        self.modes = setup_modes(self.editor, self.win)
        self.editor.setup(self.modes)
        self.win.setup(self.editor.debug_toggle_breakpoint, self.editor.theme)
        self.editor.restore_session([])

    def test_window_branding_and_theme(self):
        self.assertIn("Mu C# IDE", self.win.title)
        self.assertEqual(self.win.icon, "icon.png")
        self.assertEqual(self.editor.theme, "night")
        # Toggle theme: night -> contrast -> night (no light mode)
        self.editor.toggle_theme()
        self.assertEqual(self.editor.theme, "contrast")
        self.editor.toggle_theme()
        self.assertEqual(self.editor.theme, "night")

    def test_default_mode(self):
        self.assertEqual(self.editor.mode, "csharp")
        self.assertEqual(len(self.win.widgets), 1)

    def test_csharp_modes_switching(self):
        self.editor.change_mode("csharp_web")
        self.assertEqual(self.editor.mode, "csharp_web")
        self.assertIn("browse", self.win.button_bar.slots)

        self.editor.change_mode("csharp_test")
        self.assertEqual(self.editor.mode, "csharp_test")
        self.assertIn("debug", self.win.button_bar.slots)

        self.editor.change_mode("csharp")
        self.assertEqual(self.editor.mode, "csharp")
        self.assertIn("play", self.win.button_bar.slots)
        self.assertIn("check", self.win.button_bar.slots)
        self.assertIn("files", self.win.button_bar.slots)
        self.assertIn("snippets", self.win.button_bar.slots)

    def test_syntax_highlighting(self):
        tab = self.win.current_tab
        self.assertIsNotNone(tab)
        tab.setText("using System;\nclass Program { static void Main() { Console.WriteLine(\"Hi\"); } }")
        self.assertEqual(tab.lines(), 2)

    def test_comment_toggling(self):
        tab = self.win.current_tab
        tab.setText("Console.WriteLine(\"Hello\");")
        tab.toggle_comments()
        self.assertTrue(tab.text().startswith("// "))
        tab.toggle_comments()
        self.assertFalse(tab.text().startswith("// "))

    def test_annotations(self):
        tab = self.win.current_tab
        tab.annotate(1, "CS1002: ; expected", "error")
        self.assertTrue(tab.has_annotations)
        tab.reset_annotations()
        self.assertFalse(tab.has_annotations)

    def test_new_project_dialog(self):
        dlg = NewProjectDialog(self.win, "/tmp")
        tmpl, name, target_dir = dlg.get_details()
        self.assertEqual(tmpl, "console")
        self.assertEqual(name, "MyCSharpApp")
        self.assertEqual(target_dir, "/tmp")

    def test_dotnet_error_parsing(self):
        csharp_mode = self.modes["csharp"]
        sample_log = """
/home/user/App/Program.cs(5,12): error CS0103: The name 'xyz' does not exist in the current context [/home/user/App/App.csproj]
"""
        errors = csharp_mode._parse_dotnet_errors(sample_log)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0][0], 5)
        self.assertIn("CS0103", errors[0][1])


if __name__ == "__main__":
    unittest.main()
