import logging
import re
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QColor


class FlashLogHandler(logging.Handler, QObject):
    log_signal = pyqtSignal(str, str)  # (message, color)

    ANSI_COLOR_PATTERN = re.compile(r"\033\[(\d+;?\d*)m")
    ANSI_COLORS = {
        "30": "black",
        "31": "red",
        "32": "green",
        "33": "yellow",
        "34": "blue",
        "35": "magenta",
        "36": "cyan",
        "37": "white",
        "90": "darkGray",
        "91": "lightRed",
        "92": "lightGreen",
        "93": "lightYellow",
        "94": "lightBlue",
        "95": "lightMagenta",
        "96": "lightCyan",
        "97": "lightGray",
    }

    def __init__(self, text_edit=None, log_file_path=None):
        QObject.__init__(self)
        logging.Handler.__init__(self)
        self.text_edit = text_edit
        self.log_file = None
        self.log_file_path = None
        self.setFormatter(logging.Formatter("%(asctime)s: %(message)s"))
        if log_file_path:
            self.set_log_file(log_file_path)
        self.log_signal.connect(self._append_text)

    def emit(self, record):
        msg = self.format(record)
        # Determine color by log level first
        level_color = self._get_color(record.levelno)
        # Then parse ANSI color codes, if present, and override if found
        msg, ansi_color = self.parse_ansi_colors(msg)
        color = ansi_color if ansi_color != "white" else level_color
        if self.text_edit:
            self.log_signal.emit(msg, color)
        if self.log_file:
            self.log_file.write(msg + "\n")
            self.log_file.flush()

    def set_log_file(self, file_path):
        if self.log_file:
            self.log_file.close()
        self.log_file_path = file_path
        self.log_file = open(file_path, "a", encoding="utf-8")

    def close(self):
        if self.log_file:
            self.log_file.close()
            self.log_file = None
        super().close()

    def _append_text(self, msg, color):
        if self.text_edit:
            self.text_edit.setTextColor(QColor(color))
            self.text_edit.append(msg)
            self.text_edit.setTextColor(QColor("white"))

    def parse_ansi_colors(self, text):
        matches = self.ANSI_COLOR_PATTERN.findall(text)
        color = "white"
        for match in matches:
            color_code = match.split(";")[-1]
            if color_code in self.ANSI_COLORS:
                color = self.ANSI_COLORS[color_code]
        text = self.ANSI_COLOR_PATTERN.sub("", text)
        return text, color

    def _get_color_from_level_or_default(self, text):
        # fallback for non-ANSI: use log level if possible, else white
        # This method can be improved to extract level from text if needed
        return "white"

    def _get_color(self, levelno):
        if levelno >= logging.ERROR:
            return "red"
        elif levelno >= logging.WARNING:
            return "yellow"
        elif levelno >= logging.INFO:
            return "white"
        else:
            return "gray"


class StdoutRedirector:
    def __init__(self, logger, level=logging.INFO):
        self.logger = logger
        self.level = level

    def write(self, msg):
        msg = msg.rstrip("\n")
        if msg:
            self.logger.log(self.level, msg)

    def flush(self):
        pass

    def isatty(self):
        return False
