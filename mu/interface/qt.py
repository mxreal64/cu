"""
Qt abstraction layer supporting PyQt6 and PyQt5.
"""
try:
    from PyQt6 import QtCore, QtGui, QtWidgets
    from PyQt6.QtCore import (
        Qt,
        pyqtSignal,
        QSize,
        QRect,
        QTimer,
        QProcess,
        QProcessEnvironment,
        QDir,
        QEventLoop,
        QThread,
        QObject,
        QSharedMemory,
        QUrl,
        QLocale,
    )
    from PyQt6.QtWidgets import (
        QApplication,
        QMainWindow,
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QPlainTextEdit,
        QTextEdit,
        QToolBar,
        QTabBar,
        QTabWidget,
        QDialog,
        QDialogButtonBox,
        QLabel,
        QLineEdit,
        QPushButton,
        QComboBox,
        QListWidget,
        QListWidgetItem,
        QCheckBox,
        QMessageBox,
        QFileDialog,
        QFrame,
        QMenu,
        QTreeView,
        QSplashScreen,
        QDockWidget,
        QProgressDialog,
        QStatusBar,
        QGridLayout,
    )
    from PyQt6.QtGui import (
        QColor,
        QPainter,
        QTextFormat,
        QFont,
        QSyntaxHighlighter,
        QTextCharFormat,
        QTextCursor,
        QTextDocument,
        QKeySequence,
        QPixmap,
        QIcon,
        QMovie,
        QCursor,
        QStandardItem,
        QFontDatabase,
        QDesktopServices,
        QStandardItemModel,
        QAction,
        QShortcut,
    )

    IS_PYQT6 = True

    # Helper function to invoke dialog/app exec across Qt versions
    def exec_dialog(dlg):
        return dlg.exec()

    def exec_app(app):
        return app.exec()

    # Alignment flag compatibility
    AlignRight = Qt.AlignmentFlag.AlignRight
    AlignLeft = Qt.AlignmentFlag.AlignLeft
    AlignBottom = Qt.AlignmentFlag.AlignBottom

    # Find flags compatibility
    FindBackward = QTextDocument.FindFlag.FindBackward
    FindCaseSensitively = QTextDocument.FindFlag.FindCaseSensitively
    FindWholeWords = QTextDocument.FindFlag.FindWholeWords

    # Tool button style compatibility
    ToolButtonTextUnderIcon = Qt.ToolButtonStyle.ToolButtonTextUnderIcon
    PreventContextMenu = Qt.ContextMenuPolicy.PreventContextMenu
    CustomContextMenu = Qt.ContextMenuPolicy.CustomContextMenu

    # Line wrap mode
    NoWrap = QPlainTextEdit.LineWrapMode.NoWrap

    # Selection behavior
    SelectRows = QTreeView.SelectionBehavior.SelectRows

    # ComboBox size adjust
    AdjustToContents = QComboBox.SizeAdjustPolicy.AdjustToContents

    # Dock and Tab flags
    AllDockWidgetAreas = Qt.DockWidgetArea.AllDockWidgetAreas
    TabNorth = QTabWidget.TabPosition.North
    TabBarRightSide = QTabBar.ButtonPosition.RightSide
    TabBarLeftSide = QTabBar.ButtonPosition.LeftSide

    # Dialog Button Box and DialogCode compatibility
    ButtonBoxOk = QDialogButtonBox.StandardButton.Ok
    ButtonBoxCancel = QDialogButtonBox.StandardButton.Cancel
    ButtonBoxClose = QDialogButtonBox.StandardButton.Close
    DialogAccepted = QDialog.DialogCode.Accepted
    DialogRejected = QDialog.DialogCode.Rejected

except ImportError:
    from PyQt5 import QtCore, QtGui, QtWidgets
    from PyQt5.QtCore import (
        Qt,
        pyqtSignal,
        QSize,
        QRect,
        QTimer,
        QProcess,
        QProcessEnvironment,
        QDir,
        QEventLoop,
        QThread,
        QObject,
        QSharedMemory,
        QUrl,
        QLocale,
    )
    from PyQt5.QtWidgets import (
        QApplication,
        QMainWindow,
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QPlainTextEdit,
        QTextEdit,
        QToolBar,
        QTabBar,
        QTabWidget,
        QDialog,
        QDialogButtonBox,
        QLabel,
        QLineEdit,
        QPushButton,
        QComboBox,
        QListWidget,
        QListWidgetItem,
        QCheckBox,
        QMessageBox,
        QFileDialog,
        QFrame,
        QMenu,
        QTreeView,
        QSplashScreen,
        QDockWidget,
        QProgressDialog,
        QStatusBar,
        QGridLayout,
        QAction,
        QShortcut,
    )
    from PyQt5.QtGui import (
        QColor,
        QPainter,
        QTextFormat,
        QFont,
        QSyntaxHighlighter,
        QTextCharFormat,
        QTextCursor,
        QTextDocument,
        QKeySequence,
        QPixmap,
        QIcon,
        QMovie,
        QCursor,
        QStandardItem,
        QFontDatabase,
        QDesktopServices,
        QStandardItemModel,
    )

    IS_PYQT6 = False

    def exec_dialog(dlg):
        return dlg.exec_()

    def exec_app(app):
        return app.exec_()

    AlignRight = Qt.AlignRight
    AlignLeft = Qt.AlignLeft
    AlignBottom = Qt.AlignBottom

    FindBackward = QTextDocument.FindBackward
    FindCaseSensitively = QTextDocument.FindCaseSensitively
    FindWholeWords = QTextDocument.FindWholeWords

    ToolButtonTextUnderIcon = Qt.ToolButtonTextUnderIcon
    PreventContextMenu = Qt.PreventContextMenu
    CustomContextMenu = Qt.CustomContextMenu

    NoWrap = QPlainTextEdit.NoWrap
    SelectRows = QTreeView.SelectRows
    AdjustToContents = QComboBox.AdjustToContents
    AllDockWidgetAreas = Qt.AllDockWidgetAreas
    TabNorth = QTabWidget.North
    TabBarRightSide = QTabBar.RightSide
    TabBarLeftSide = QTabBar.LeftSide
    ButtonBoxOk = QDialogButtonBox.Ok
    ButtonBoxCancel = QDialogButtonBox.Cancel
    ButtonBoxClose = QDialogButtonBox.Close
    DialogAccepted = QDialog.Accepted
    DialogRejected = QDialog.Rejected
