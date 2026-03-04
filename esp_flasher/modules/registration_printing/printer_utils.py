import platform


def list_available_printers():
    """Detects available printers based on OS and returns a list."""
    system = platform.system()

    if system == "Linux":
        return _list_linux_printers()
    elif system == "Windows":
        return _list_windows_printers()
    else:
        return []


def _list_linux_printers():
    """Lists available printers using lpstat (CUPS)."""
    try:
        import subprocess

        result = subprocess.run(["lpstat", "-p"], stdout=subprocess.PIPE, text=True)
        printers = [
            line.split()[1] for line in result.stdout.splitlines() if "printer" in line
        ]
        return printers
    except Exception:
        return []


def _list_windows_printers():
    """Lists available printers on Windows using win32print."""
    try:
        import win32print

        printers = [printer[2] for printer in win32print.EnumPrinters(2)]
        return printers
    except Exception:
        return []
