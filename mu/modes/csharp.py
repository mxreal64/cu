"""
C# Modes for Mu Editor.

Provides:
- CSharpMode: C# Application & Console Mode (Build, Run, Test, NuGet, Format, Clean)
- CSharpWebMode: C# Web & ASP.NET Core Mode
- CSharpTestMode: C# Test Runner Mode
- CSharpReplMode: C# Interactive REPL Mode
"""
import os
import re
import shutil
import logging
import subprocess
from mu.interface.qt import (
    QProcess,
    QTimer,
    Qt,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QListWidget,
    QMessageBox,
    QPlainTextEdit,
    QDialogButtonBox,
    QFileDialog,
    ButtonBoxOk,
    ButtonBoxCancel,
    DialogAccepted,
    exec_dialog,
)
from mu.modes.base import BaseMode
from mu.resources import load_icon

logger = logging.getLogger(__name__)


def find_project_or_file(path_or_dir):
    """
    Finds the nearest .csproj, .sln, or returns the file directory.
    """
    if not path_or_dir:
        return None
    curr = os.path.abspath(path_or_dir)
    if os.path.isfile(curr):
        curr = os.path.dirname(curr)
    while curr and curr != os.path.dirname(curr):
        for f in os.listdir(curr):
            if f.endswith(".csproj") or f.endswith(".sln"):
                return curr
        curr = os.path.dirname(curr)
    return None


class NewProjectDialog(QDialog):
    """
    Wizard for scaffolding a new C# project with `dotnet new`.
    """

    def __init__(self, parent=None, default_dir=""):
        super().__init__(parent)
        self.setWindowTitle("New C# Project")
        self.setMinimumWidth(480)
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Select C# Project Template:"))
        self.template_combo = QComboBox()
        self.template_combo.addItem("Console Application (console)", "console")
        self.template_combo.addItem("Web API / ASP.NET (webapi)", "webapi")
        self.template_combo.addItem("Empty Web Application (web)", "web")
        self.template_combo.addItem("Class Library (classlib)", "classlib")
        self.template_combo.addItem("xUnit Test Project (xunit)", "xunit")
        self.template_combo.addItem("NUnit Test Project (nunit)", "nunit")
        self.template_combo.addItem("Blazor Web App (blazor)", "blazor")
        layout.addWidget(self.template_combo)

        layout.addWidget(QLabel("Project Name:"))
        self.name_edit = QLineEdit("MyCSharpApp")
        layout.addWidget(self.name_edit)

        layout.addWidget(QLabel("Target Directory:"))
        dir_layout = QHBoxLayout()
        self.dir_edit = QLineEdit(default_dir)
        dir_layout.addWidget(self.dir_edit)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_dir)
        dir_layout.addWidget(browse_btn)
        layout.addLayout(dir_layout)

        btn_box = QDialogButtonBox(ButtonBoxOk | ButtonBoxCancel)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def _browse_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Select Directory", self.dir_edit.text())
        if d:
            self.dir_edit.setText(d)

    def get_details(self):
        return (
            self.template_combo.currentData(),
            self.name_edit.text().strip(),
            self.dir_edit.text().strip(),
        )


class NuGetDialog(QDialog):
    """
    NuGet Package Manager dialog for adding/removing NuGet dependencies.
    """

    def __init__(self, project_dir, parent=None):
        super().__init__(parent)
        self.project_dir = project_dir
        self.setWindowTitle("NuGet Package Manager")
        self.setMinimumSize(540, 380)
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel(f"Project: {os.path.basename(project_dir)}"))

        add_layout = QHBoxLayout()
        self.package_edit = QLineEdit()
        self.package_edit.setPlaceholderText("Package ID (e.g. Newtonsoft.Json, Dapper)")
        add_layout.addWidget(self.package_edit)
        self.add_btn = QPushButton("Add Package")
        self.add_btn.clicked.connect(self._add_package)
        add_layout.addWidget(self.add_btn)
        layout.addLayout(add_layout)

        layout.addWidget(QLabel("Installed Packages / Output:"))
        self.output_text = QPlainTextEdit()
        self.output_text.setReadOnly(True)
        layout.addWidget(self.output_text)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        self._list_packages()

    def _list_packages(self):
        self.output_text.appendPlainText("Querying installed packages...\n")
        try:
            res = subprocess.run(
                ["dotnet", "list", "package"],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
            )
            self.output_text.appendPlainText(res.stdout or res.stderr)
        except Exception as e:
            self.output_text.appendPlainText(f"Error listing packages: {e}\n")

    def _add_package(self):
        pkg = self.package_edit.text().strip()
        if not pkg:
            return
        self.output_text.appendPlainText(f"\nAdding package '{pkg}' via dotnet add package...")
        self.add_btn.setEnabled(False)
        QTimer.singleShot(10, lambda: self._run_add(pkg))

    def _run_add(self, pkg):
        try:
            res = subprocess.run(
                ["dotnet", "add", "package", pkg],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
            )
            self.output_text.appendPlainText(res.stdout or res.stderr)
            self.package_edit.clear()
        except Exception as e:
            self.output_text.appendPlainText(f"Error adding package: {e}\n")
        finally:
            self.add_btn.setEnabled(True)


class CSharpMode(BaseMode):
    """
    C# Application & Console Mode for Mu.
    Supports building, running, testing, formatting, and NuGet management.
    """

    name = "C# Application"
    short_name = "csharp"
    description = "Create, build and run modern C# (.NET) applications."
    icon = "run"
    file_extensions = [".cs", ".csproj", ".sln", ".json", ".xaml"]
    code_template = """// C# Application
using System;

Console.WriteLine("Hello from C# in Mu!");
"""

    def __init__(self, editor, view):
        super().__init__(editor, view)
        self.process = None

    def actions(self):
        return [
            {
                "name": "play",
                "display_name": "Run",
                "description": "Run the C# application (dotnet run).",
                "handler": self.run,
                "shortcut": "F5",
            },
            {
                "name": "check",
                "display_name": "Build",
                "description": "Build project and check for compiler errors (dotnet build).",
                "handler": self.check,
                "shortcut": "F6",
            },
            {
                "name": "debug",
                "display_name": "Test",
                "description": "Run unit tests (dotnet test).",
                "handler": self.test,
                "shortcut": "F7",
            },
            {
                "name": "files",
                "display_name": "New Proj",
                "description": "Create a new C# project template (dotnet new).",
                "handler": self.new_proj,
                "shortcut": "Ctrl+Shift+N",
            },
            {
                "name": "snippets",
                "display_name": "NuGet",
                "description": "Manage NuGet packages for this project.",
                "handler": self.nuget,
                "shortcut": "Ctrl+Shift+P",
            },
            {
                "name": "tidy",
                "display_name": "Format",
                "description": "Format C# code (dotnet format).",
                "handler": self.tidy,
                "shortcut": "F10",
            },
        ]

    def get_working_dir(self):
        if self.view.current_tab and self.view.current_tab.path:
            p = find_project_or_file(self.view.current_tab.path)
            if p:
                return p
            return os.path.dirname(self.view.current_tab.path)
        return self.workspace_dir()

    def run(self):
        """
        Execute `dotnet run` in the project directory using the bottom ProcessPane.
        """
        if self.view.process_pane:
            self.stop()
            return

        working_dir = self.get_working_dir()
        self.editor.save()

        # Ensure project file exists or create a simple console csproj if single .cs file
        if self.view.current_tab and self.view.current_tab.path:
            if not find_project_or_file(working_dir):
                self._ensure_single_file_csproj(working_dir)

        logger.info(f"Running C# in {working_dir}")
        self.view.add_python_process(
            ["dotnet", "run"],
            cwd=working_dir,
            name="C# Output",
        )
        self.set_buttons(play=True, check=False)

    def stop(self):
        """
        Stop running C# process.
        """
        if self.view.process_pane:
            self.view.remove_python_process()
        self.set_buttons(play=True, check=True)
        self.return_focus_to_current_tab()

    def check(self):
        """
        Run `dotnet build --nologo` to report compilation errors and annotate editor lines.
        """
        working_dir = self.get_working_dir()
        self.editor.save()

        if self.view.current_tab and self.view.current_tab.path:
            if not find_project_or_file(working_dir):
                self._ensure_single_file_csproj(working_dir)

        self.view.reset_annotations()
        try:
            res = subprocess.run(
                ["dotnet", "build", "--nologo", "-clp:NoSummary"],
                cwd=working_dir,
                capture_output=True,
                text=True,
            )
            output = res.stdout + res.stderr
            errors = self._parse_dotnet_errors(output)

            if errors:
                for line_no, msg in errors:
                    self.view.annotate_code([{"line": line_no, "message": msg}], "error")
                self.view.show_annotations()
                self.view.show_message(
                    "Build Failed",
                    f"Found {len(errors)} error(s) during build:\n" + "\n".join([f"Line {l}: {m}" for l, m in errors[:5]]),
                )
            else:
                self.view.show_message("Build Succeeded", "Project built successfully with 0 errors!")
        except Exception as e:
            self.view.show_message("Build Error", str(e))

    def _parse_dotnet_errors(self, output):
        # Format: file.cs(line,col): error CSxxxx: message
        pattern = re.compile(r"\((?P<line>\d+),\d+\):\s+(?P<msg>(?:error|fatal error|warning)\s+[A-Za-z0-9]+:\s+.+)")
        results = []
        for line in output.splitlines():
            match = pattern.search(line)
            if match:
                try:
                    line_no = int(match.group("line"))
                    msg = match.group("msg").strip()
                    results.append((line_no, msg))
                except ValueError:
                    pass
        return results

    def _ensure_single_file_csproj(self, dir_path):
        csproj_path = os.path.join(dir_path, "App.csproj")
        if not os.path.exists(csproj_path):
            content = """<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net10.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
  </PropertyGroup>
</Project>
"""
            with open(csproj_path, "w", encoding="utf-8") as f:
                f.write(content)

    def test(self):
        """
        Run `dotnet test`
        """
        working_dir = self.get_working_dir()
        self.editor.save()
        self.view.add_python_process(
            ["dotnet", "test", "--nologo"],
            cwd=working_dir,
            name="C# Tests",
        )

    def new_proj(self):
        """
        Launch New Project Wizard.
        """
        dlg = NewProjectDialog(self.view, self.workspace_dir())
        if exec_dialog(dlg) == DialogAccepted:
            tmpl, name, target_dir = dlg.get_details()
            if not os.path.exists(target_dir):
                os.makedirs(target_dir, exist_ok=True)
            proj_dir = os.path.join(target_dir, name)
            os.makedirs(proj_dir, exist_ok=True)

            res = subprocess.run(
                ["dotnet", "new", tmpl, "-n", name],
                cwd=proj_dir,
                capture_output=True,
                text=True,
            )
            if res.returncode == 0:
                # Open Program.cs or primary file
                for root, _, files in os.walk(proj_dir):
                    for f in files:
                        if f.endswith(".cs"):
                            self.editor.direct_load(os.path.join(root, f))
                            break
                self.view.show_message("Project Created", f"Successfully created {tmpl} project '{name}'!")
            else:
                self.view.show_message("Error", f"Failed to create project:\n{res.stderr or res.stdout}")

    def nuget(self):
        """
        Manage NuGet packages for active project.
        """
        working_dir = self.get_working_dir()
        dlg = NuGetDialog(working_dir, self.view)
        exec_dialog(dlg)

    def tidy(self):
        """
        Run `dotnet format`.
        """
        working_dir = self.get_working_dir()
        self.editor.save()
        res = subprocess.run(["dotnet", "format"], cwd=working_dir, capture_output=True, text=True)
        if self.view.current_tab and self.view.current_tab.path:
            # Reload current tab
            path = self.view.current_tab.path
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    self.view.current_tab.setText(f.read())
        self.view.show_message("Format Complete", "C# code formatting applied.")


class CSharpWebMode(CSharpMode):
    """
    C# Web API & ASP.NET Core Mode.
    """

    name = "C# Web / ASP.NET"
    short_name = "csharp_web"
    description = "Develop, run and test ASP.NET Core web apps and APIs."
    icon = "web"
    code_template = """var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();

app.MapGet("/", () => "Hello from ASP.NET Core in Mu!");

app.Run();
"""

    def actions(self):
        return [
            {
                "name": "play",
                "display_name": "Run",
                "description": "Start the ASP.NET Core web server.",
                "handler": self.run,
                "shortcut": "F5",
            },
            {
                "name": "check",
                "display_name": "Build",
                "description": "Build ASP.NET Core project.",
                "handler": self.check,
                "shortcut": "F6",
            },
            {
                "name": "browse",
                "display_name": "Browse",
                "description": "Open default web endpoint in browser.",
                "handler": self.browse,
                "shortcut": "F8",
            },
            {
                "name": "snippets",
                "display_name": "NuGet",
                "description": "Manage NuGet packages.",
                "handler": self.nuget,
                "shortcut": "Ctrl+Shift+P",
            },
            {
                "name": "tidy",
                "display_name": "Format",
                "description": "Format C# code.",
                "handler": self.tidy,
                "shortcut": "F10",
            },
        ]

    def browse(self):
        import webbrowser
        webbrowser.open("http://localhost:5000")


class CSharpTestMode(CSharpMode):
    """
    C# Test Runner Mode.
    """

    name = "C# Test Runner"
    short_name = "csharp_test"
    description = "Run and debug unit test suites (xUnit, NUnit, MSTest)."
    icon = "check"
    code_template = """using Xunit;

public class SampleTests
{
    [Fact]
    public void TestPassing()
    {
        Assert.Equal(4, 2 + 2);
    }
}
"""

    def actions(self):
        return [
            {
                "name": "debug",
                "display_name": "Run Tests",
                "description": "Execute all tests (dotnet test).",
                "handler": self.test,
                "shortcut": "F7",
            },
            {
                "name": "check",
                "display_name": "Build",
                "description": "Build test project.",
                "handler": self.check,
                "shortcut": "F6",
            },
            {
                "name": "tidy",
                "display_name": "Format",
                "description": "Format C# code.",
                "handler": self.tidy,
                "shortcut": "F10",
            },
        ]


class CSharpReplMode(CSharpMode):
    """
    C# Interactive REPL Mode.
    """

    name = "C# Interactive"
    short_name = "csharp_repl"
    description = "Evaluate C# code interactively in a REPL session."
    icon = "repl"

    def actions(self):
        return [
            {
                "name": "repl",
                "display_name": "REPL",
                "description": "Toggle C# interactive REPL session.",
                "handler": self.toggle_repl,
                "shortcut": "F5",
            },
            {
                "name": "tidy",
                "display_name": "Format",
                "description": "Format C# code.",
                "handler": self.tidy,
                "shortcut": "F10",
            },
        ]

    def toggle_repl(self):
        if self.view.process_pane:
            self.stop()
        else:
            # Check for csharp or csi or dotnet-interactive
            repl_cmd = "csharp" if shutil.which("csharp") else ("csi" if shutil.which("csi") else "dotnet")
            args = [repl_cmd] if repl_cmd != "dotnet" else ["dotnet", "fsi"]
            self.view.add_python_process(
                args,
                cwd=self.workspace_dir(),
                name="C# Interactive REPL",
            )
