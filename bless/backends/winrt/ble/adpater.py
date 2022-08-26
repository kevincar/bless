import winreg

from pysetupdi import devices
from pywin32 import win32file, win32api
from pywin32.win32con import GENERIC_WRITE, OPEN_EXISTING


class BLEAdapter:
    def __init__(self):
        self._dev: int = None
        self._adapter_name: str = get_bluetooth_adapter()
        self._device_guid: str = "{a5dcbf10-6530-11d2-901f-00c04fb951ed}"
        self._device_name_: str = self._adapter_name.replace("\\", "#")
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
        key = winreg.OpenKeyEx(
            winreg.HKEY_LOCAL_MACHINE, local_name_key, 0, winreg.KEY_SET_VALUE
        )

        winreg.SetValueEx(
            key, "Local Name", 0, winreg.REG_BINARY, local_name
        )
        winreg.CloseKey(key)

    def _restart_device(self):
        os_major_version: int = win32api.GetVersionEx()[0]
        control_code: int = 0x220fd4 if os_major_version < 6 else 0x411008
        reload_command: int = 4
        win32file.DeviceIoControl(self._dev, control_code, reload_command, 0)


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
