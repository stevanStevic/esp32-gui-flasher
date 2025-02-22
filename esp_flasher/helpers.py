from __future__ import print_function

import os
import sys

import serial
import esptool

# pylint: disable=unspecified-encoding,consider-using-with
DEVNULL = open(os.devnull, "w")


def list_serial_ports():
    return esptool.get_port_list()


def prevent_print(func, *args, **kwargs):
    orig_sys_stdout = sys.stdout
    sys.stdout = DEVNULL
    try:
        return func(*args, **kwargs)
    except serial.SerialException as err:
        from esp_flasher.common import EspflasherError

        raise EspflasherError("Serial port closed: {}".format(err))
    finally:
        sys.stdout = orig_sys_stdout
        sys.stdout.isatty = lambda: False
        pass
