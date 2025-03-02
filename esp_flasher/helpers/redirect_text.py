from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QTextCursor


class RedirectText(QObject):
    text_written = pyqtSignal(str)

    def __init__(self, text_edit):
        super().__init__()
        self._out = text_edit
        self._line = ""
        self._bold = False
        self._italic = False
        self._underline = False
        self._foreground = None
        self._background = None
        self._secret = False
        self.text_written.connect(self._append_text)

    def write(self, string):
        self.text_written.emit(string)

    def flush(self):
        pass

    def isatty(self):
        """Pretend to be a terminal to avoid crashes."""
        return False

    def _append_text(self, text):
        cursor = self._out.textCursor()
        self._out.moveCursor(QTextCursor.End)
        self._out.insertPlainText(text)
        self._out.setTextCursor(cursor)
