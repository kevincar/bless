import win32file  # type: ignore
import win32api  # type: ignore

from typing import cast
from pysetupdi import devices  # type: ignore
from win32con import GENERIC_WRITE, OPEN_EXISTING  # type: ignore
from winreg import (  # type: ignore
    HKEY_LOCAL_MACHINE,
    KEY_SET_VALUE,
    REG_BINARY,
    OpenKeyEx,
    SetValueEx,
    CloseKey
)


class BLEAdapter:
    def __init__(self: "BLEAdapter"):
        self._adapter_name: str = get_bluetooth_adapter()
        self._device_guid: str = "{a5dcbf10-6530-11d2-901f-00c04fb951ed}"
        self._device_name: str = self._adapter_name.replace("\\", "#")
        self._filename: str = "\\\\.\\" + self._device_name + "#" + self._device_guid

        self._dev: int = win32file.CreateFile(
            self._filename, GENERIC_WRITE, 0, None, OPEN_EXISTING, 0, None
        )

        if self._dev == -1:
            raise Exception("Failed to open a connection to the bluetooth adapter")

    def set_local_name(self, local_name: str):
        self._set_registry_name(local_name)
        self._restart_device()

    def _set_registry_name(self, local_name: str):
        local_name_key: str = (
            f"SYSTEM\\ControlSet001\\Enum\\{self._adapter_name}\\Device Parameters"
        )
        key = OpenKeyEx(
            HKEY_LOCAL_MACHINE, local_name_key, 0, KEY_SET_VALUE
        )

        SetValueEx(
            key,
            "Local Name",
            0,
            REG_BINARY,
            cast(str, bytes(local_name, "utf-8"))
        )
        CloseKey(key)

    def _restart_device(self: "BLEAdapter"):
        os_major_version: int = win32api.GetVersionEx()[0]
        control_code: int = 0x220fd4 if os_major_version < 6 else 0x411008
        reload_command: int = 4
        win32file.DeviceIoControl(
            self._dev, control_code, reload_command.to_bytes(4, byteorder="little"), 0
        )


def get_bluetooth_adapter() -> str:
    """
    Retrieve the instance id of the bluetooth device on the system

    Returns
    -------
    str
        The string that points to the device IO file on win32
    """
    bluetooth_device_guid: str = "{e0cbf06c-cd8b-4647-bb8a-263b43f0f974}"
    for bluetooth_device in devices(bluetooth_device_guid):
        if bluetooth_device._instance_id[:3] == "USB":
            return bluetooth_device._instance_id
    return ""
