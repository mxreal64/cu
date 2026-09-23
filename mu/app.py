"""
Mu - Modern C# IDE with Mu's Iconic UI.

Copyright (c) 2015-2026 Nicholas H.Tollervey and contributors.
"""
import logging
from logging.handlers import TimedRotatingFileHandler
import os
import time
import platform
import traceback
import struct
import sys
import urllib
import webbrowser
import base64

from mu.interface.qt import (
    Qt,
    QEventLoop,
    QThread,
    QObject,
    pyqtSignal,
    QSharedMemory,
    QApplication,
    QSplashScreen,
    AlignBottom,
    AlignLeft,
    exec_app,
)

from . import i18n
from . import __version__
from .logic import Editor, LOG_FILE, LOG_DIR, ENCODING
from .interface import Window
from .resources import load_icon, load_movie, load_pixmap
from .modes import (
    CSharpMode,
    CSharpWebMode,
    CSharpTestMode,
    CSharpReplMode,
)
from .interface.themes import NIGHT_STYLE, DAY_STYLE, CONTRAST_STYLE
from . import settings


class AnimatedSplash(QSplashScreen):
    """
    An animated splash screen for gifs. Includes a text area for logging output.
    """

    def __init__(self, animation, parent=None):
        self.log_lines = 4
        self.log = []
        self.animation = animation
        self.animation.frameChanged.connect(self.set_frame)
        super().__init__(self.animation.currentPixmap())
        self.setEnabled(False)
        self.animation.start()

    def set_frame(self):
        pixmap = self.animation.currentPixmap()
        self.setPixmap(pixmap)
        self.setMask(pixmap.mask())

    def draw_log(self, text):
        self.log.append(text)
        self.log = self.log[-self.log_lines :]
        if self.log:
            self.draw_text("\n".join(self.log))

    def draw_text(self, text):
        if text:
            self.showMessage(text, AlignBottom | AlignLeft)

    def failed(self, text):
        self.animation.stop()
        pixmap = load_pixmap("splash_fail.png")
        self.setPixmap(pixmap)
        lines = text.split("\n")
        lines.append(
            "This screen will close in a few seconds."
        )
        lines = lines[-12:]
        self.draw_text("\n".join(lines))


class StartupWorker(QObject):
    """
    Worker for startup initialization.
    """

    finished = pyqtSignal()
    failed = pyqtSignal(str)
    display_text = pyqtSignal(str)

    def run(self):
        try:
            self.display_text.emit("Initializing C# IDE...")
            time.sleep(0.3)
            self.finished.emit()
        except Exception as ex:
            stack = traceback.extract_stack()[:-1]
            msg = "\n".join(traceback.format_list(stack))
            msg += "\n\n" + traceback.format_exc()
            self.failed.emit(msg)
            time.sleep(3)
            self.finished.emit()
            raise ex


def excepthook(*exc_args):
    logging.error("Unrecoverable error", exc_info=(exc_args))
    _shared_memory.release()
    if exc_args[0] != KeyboardInterrupt:
        sys.__excepthook__(*exc_args)
        sys.exit(1)
    else:
        sys.exit(0)


def setup_exception_handler():
    sys.excepthook = excepthook


def setup_logging():
    os.makedirs(LOG_DIR, exist_ok=True)
    log_fmt = "%(asctime)s - %(name)s:%(lineno)d(%(funcName)s) %(levelname)s: %(message)s"
    formatter = logging.Formatter(log_fmt)
    handler = TimedRotatingFileHandler(
        LOG_FILE, when="midnight", backupCount=5, delay=0, encoding=ENCODING
    )
    handler.setFormatter(formatter)
    handler.setLevel(logging.DEBUG)

    log = logging.getLogger()
    log.setLevel(logging.DEBUG)
    log.addHandler(handler)

    if "MU_LOG_TO_STDOUT" in os.environ:
        stdout_handler = logging.StreamHandler()
        stdout_handler.setFormatter(formatter)
        stdout_handler.setLevel(logging.DEBUG)
        log.addHandler(stdout_handler)


def setup_modes(editor, view):
    return {
        "csharp": CSharpMode(editor, view),
        "csharp_web": CSharpWebMode(editor, view),
        "csharp_test": CSharpTestMode(editor, view),
        "csharp_repl": CSharpReplMode(editor, view),
    }


class MutexError(BaseException):
    pass


class SharedMemoryMutex(object):
    NAME = "mu-csharp-tex"

    def __init__(self):
        sharedAppName = self.NAME
        if "MU_TEST_SUPPORT_RANDOM_APP_NAME_EXT" in os.environ:
            sharedAppName += os.environ["MU_TEST_SUPPORT_RANDOM_APP_NAME_EXT"]
        self._shared_memory = QSharedMemory(sharedAppName)

    def __enter__(self):
        self._shared_memory.lock()
        return self

    def __exit__(self, *args, **kwargs):
        self._shared_memory.unlock()

    def acquire(self):
        self._shared_memory.attach()
        self._shared_memory.detach()
        if self._shared_memory.attach():
            pid = struct.unpack("q", self._shared_memory.data()[:8])
            raise MutexError("MUTEX: Mu is already running with pid %d" % pid)
        else:
            self._shared_memory.create(8)
            self._shared_memory.data()[:8] = struct.pack("q", os.getpid())

    def release(self):
        self._shared_memory.detach()


_shared_memory = SharedMemoryMutex()


def is_linux_wayland():
    if platform.system() == "Linux":
        for env_var in ("XDG_SESSION_TYPE", "WAYLAND_DISPLAY"):
            if "wayland" in os.environ.get(env_var, "").lower():
                return True
    return False


def check_only_running_once():
    try:
        with _shared_memory:
            _shared_memory.acquire()
    except MutexError as exc:
        [message] = exc.args
        logging.error(message)
        sys.exit(2)


def run():
    setup_logging()
    logging.info("\n\n-----------------\n\nStarting Mu C# IDE {}".format(__version__))
    logging.info(platform.uname())
    logging.info("Process id: {}".format(os.getpid()))
    logging.info("Language code: {}".format(i18n.language_code))
    setup_exception_handler()
    check_only_running_once()

    settings.init()

    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    if hasattr(Qt, "AA_EnableHighDpiScaling"):
        QApplication.setAttribute(getattr(Qt, "AA_EnableHighDpiScaling"))
    if hasattr(Qt, "AA_UseHighDpiPixmaps"):
        QApplication.setAttribute(getattr(Qt, "AA_UseHighDpiPixmaps"))
    os.environ["QT_MAC_WANTS_LAYER"] = "1"

    if is_linux_wayland():
        if "QT_QPA_PLATFORM" not in os.environ:
            logging.info("Wayland detected, setting QT_QPA_PLATFORM=wayland")
            os.environ["QT_QPA_PLATFORM"] = "wayland"

    app = QApplication(sys.argv)
    app.setApplicationName("mu-csharp")
    app.setDesktopFileName("mu.codewith.editor")
    app.setApplicationVersion(__version__)
    if hasattr(Qt, "AA_DontShowIconsInMenus"):
        app.setAttribute(getattr(Qt, "AA_DontShowIconsInMenus"))

    def splash_context():
        splash = AnimatedSplash(load_movie("splash_screen"))
        splash.show()
        initLoop = QEventLoop()
        thread = QThread()
        worker = StartupWorker()
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        worker.display_text.connect(splash.draw_log)
        worker.failed.connect(splash.failed)
        thread.finished.connect(initLoop.quit)
        thread.finished.connect(thread.deleteLater)
        thread.start()
        if hasattr(initLoop, "exec"):
            initLoop.exec()
        else:
            initLoop.exec_()
        splash.close()
        splash.deleteLater()

    splash_context()

    editor_window = Window()

    @editor_window.load_theme.connect
    def load_theme(theme):
        if theme == "contrast":
            app.setStyleSheet(CONTRAST_STYLE)
        else:
            app.setStyleSheet(NIGHT_STYLE)

    app.setWindowIcon(load_icon("icon.png"))
    editor = Editor(view=editor_window)
    editor.setup(setup_modes(editor, editor_window))
    editor_window.closeEvent = editor.quit
    editor_window.setup(editor.debug_toggle_breakpoint, editor.theme)
    editor_window.connect_tab_rename(editor.rename_tab, "Ctrl+Shift+S")
    editor_window.connect_find_replace(editor.find_replace, "Ctrl+F")
    find_again_handlers = (editor.find_again, editor.find_again_backward)
    editor_window.connect_find_again(find_again_handlers, "F3")
    editor_window.connect_toggle_comments(editor.toggle_comments, "Ctrl+K")
    editor.connect_to_status_bar(editor_window.status_bar)

    editor.restore_session(sys.argv[1:])

    exit_status = exec_app(app)
    _shared_memory.release()
    sys.exit(exit_status)
