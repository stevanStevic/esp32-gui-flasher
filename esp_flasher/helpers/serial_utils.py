from esp_flasher.helpers.helpers import Esp_flasherError
import esptool


def list_serial_ports():
    return esptool.get_port_list()


def select_port(args):
    if args.port:
        print(f"Using '{args.port}' as serial port.")
        return args.port

    ports = list_serial_ports()
    if not ports:
        raise Esp_flasherError("No serial port found!")

    if len(ports) == 1:
        print(f"Auto-detected serial port: {ports[0][0]}")
        return ports[0][0]

    print("Found multiple serial ports:")
    for port, desc in ports:
        print(f" * {port} ({desc})")
    print("Please specify one using the --port argument.")
    raise Esp_flasherError()
