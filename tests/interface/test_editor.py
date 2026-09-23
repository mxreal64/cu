"""
Tests for C# EditorPane and Syntax Highlighter.
"""
import os
import unittest
from mu.interface.qt import QApplication
from mu.interface.editor import EditorPane, CSharpHighlighter

app = QApplication.instance() or QApplication([])


class TestEditorPane(unittest.TestCase):
    def test_editor_creation(self):
        pane = EditorPane(
            "/tmp/TestApp/Program.cs",
            "using System;\nConsole.WriteLine(\"Hello\");\n",
        )
        self.assertEqual(pane.lines(), 3)
        self.assertIn("Program.cs", pane.label)
        self.assertIn("Program.cs", pane.title)
        self.assertFalse(pane.isModified())

    def test_syntax_highlighter(self):
        pane = EditorPane(
            "/tmp/TestApp/Program.cs",
            "namespace MyApp;\nclass Program { static void Main() { string x = \"test\"; } }",
        )
        self.assertIsNotNone(pane.highlighter)
        pane.set_theme("night")
        self.assertEqual(pane.theme_name, "night")
        pane.set_theme("contrast")
        self.assertEqual(pane.theme_name, "contrast")
        pane.set_theme("day")
        self.assertEqual(pane.theme_name, "night")  # Light mode ripped out, defaults to night

    def test_annotations(self):
        pane = EditorPane("/tmp/TestApp/Program.cs", "Console.WriteLine(42);\n")
        pane.annotate(1, "Syntax Error", "error")
        self.assertTrue(pane.has_annotations)
        self.assertIn(1, pane.check_indicators["error"])
        pane.clear_annotations()
        self.assertFalse(pane.has_annotations)


if __name__ == "__main__":
    unittest.main()
