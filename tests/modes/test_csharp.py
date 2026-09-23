"""
Tests for C# modes in Mu.
"""
import unittest
from unittest.mock import MagicMock
from mu.modes import CSharpMode, CSharpWebMode, CSharpTestMode, CSharpReplMode
from mu.modes.csharp import find_project_or_file


class TestCSharpModes(unittest.TestCase):
    def test_csharp_mode_actions(self):
        editor = MagicMock()
        view = MagicMock()
        mode = CSharpMode(editor, view)
        actions = mode.actions()
        action_names = [a["name"] for a in actions]
        self.assertIn("play", action_names)
        self.assertIn("check", action_names)
        self.assertIn("debug", action_names)
        self.assertIn("files", action_names)
        self.assertIn("snippets", action_names)
        self.assertIn("tidy", action_names)

    def test_csharp_web_mode(self):
        editor = MagicMock()
        view = MagicMock()
        mode = CSharpWebMode(editor, view)
        actions = mode.actions()
        action_names = [a["name"] for a in actions]
        self.assertIn("browse", action_names)

    def test_csharp_test_mode(self):
        editor = MagicMock()
        view = MagicMock()
        mode = CSharpTestMode(editor, view)
        actions = mode.actions()
        action_names = [a["name"] for a in actions]
        self.assertIn("debug", action_names)

    def test_csharp_error_parsing(self):
        editor = MagicMock()
        view = MagicMock()
        mode = CSharpMode(editor, view)
        sample_output = """
/path/to/Program.cs(12,25): error CS1002: ; expected [/path/to/App.csproj]
/path/to/Program.cs(18,10): error CS0103: The name 'foo' does not exist in the current context [/path/to/App.csproj]
"""
        errors = mode._parse_dotnet_errors(sample_output)
        self.assertEqual(len(errors), 2)
        self.assertEqual(errors[0][0], 12)
        self.assertIn("; expected", errors[0][1])
        self.assertEqual(errors[1][0], 18)


if __name__ == "__main__":
    unittest.main()
