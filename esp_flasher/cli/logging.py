import serial
from datetime import datetime

RUN_LOG = True  # Global flag to control logging execution


def stop_logs():
    global RUN_LOG
    RUN_LOG = False


def show_logs(port):
    global RUN_LOG
    RUN_LOG = True

    print("Displaying logs:")
    try:
        with serial.Serial(port, baudrate=115200) as serial_port:
            while RUN_LOG:
                raw = serial_port.readline()
                text = raw.decode(errors="ignore").strip()
                print(f"[{datetime.now().time().strftime('%H:%M:%S')}] {text}")
    except serial.SerialException:
        print("Serial port closed or unavailable!")
