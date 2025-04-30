from PyQt5.QtCore import QThread, pyqtSignal
import serial
import time
import re


class LogThread(QThread):
    log_signal = pyqtSignal(str, str)  # Now sends (text, color)
    error_signal = pyqtSignal(str)

    # Regex to match ANSI color escape codes
    ANSI_COLOR_PATTERN = re.compile(r"\033\[(\d+;?\d*)m")

    # Map ANSI color codes to Qt color names
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

    def __init__(self, port):
        super().__init__()
        self._port = port
        self._running = False
        self._default_color = "white"

    def run(self):
        """Reads logs from the ESP device in a non-blocking way."""
        self._running = True

        try:
            with serial.Serial(self._port, baudrate=115200, timeout=1) as serial_port:
                # Prevent ESP32 from staying in bootloader mode
                serial_port.setDTR(False)
                serial_port.setRTS(False)
                time.sleep(0.1)  # Give it a moment to settle

                while self._running:
                    if serial_port.in_waiting > 0:  # Check if data is available
                        raw = serial_port.readline()
                        text = raw.decode(errors="ignore").strip()
                        text, color = self.parse_ansi_colors(text)  # Decode color
                        self.log_signal.emit(text, color)  # Emit formatted log
        except serial.SerialException as e:
            self.error_signal.emit(f"Serial Error: {str(e)}")
        except Exception as e:
            self.error_signal.emit(f"Log Error: {str(e)}")

    def parse_ansi_colors(self, text):
        """Extracts ANSI colors and returns cleaned text with associated color."""
        matches = self.ANSI_COLOR_PATTERN.findall(text)

        color = self._default_color
        for match in matches:
            color_code = match.split(";")[-1]  # Extract last code in sequence
            if color_code in self.ANSI_COLORS:
                color = self.ANSI_COLORS[color_code]

        text = self.ANSI_COLOR_PATTERN.sub("", text)  # Remove ANSI codes
        return text, color

    def start_logging(self):
        """Starts the logging process inside the thread."""
        if not self.isRunning():
            self.start()  # Start the QThread

    def stop_logging(self):
        """Stops log monitoring gracefully."""
        if self.isRunning():
            self._running = False
            self.wait()  # Ensure thread exits properly
            self.log_signal.emit("Logging stopped.", self._default_color)
