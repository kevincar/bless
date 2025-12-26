import platform
import warnings
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class BlessAdvertisementData:
    """
    Generic advertisement data for BLE backends.
    """

    local_name: Optional[str] = None
    service_uuids: Optional[List[str]] = None
    manufacturer_data: Optional[Dict[int, bytes]] = None
    service_data: Optional[Dict[str, bytes]] = None
    is_connectable: Optional[bool] = None
    is_discoverable: Optional[bool] = None
    tx_power: Optional[int] = None

    def __post_init__(self) -> None:
        """
        Warn when fields are provided that are not used by the current OS backend.
        """
        system = platform.system()
        if system == "Darwin":
            unused = self._unused_fields({"local_name", "service_uuids"})
        elif system == "Windows":
            unused = self._unused_fields(
                {"local_name", "is_connectable", "is_discoverable"}
            )
        elif system == "Linux":
            unused = self._unused_fields(
                {
                    "local_name",
                    "service_uuids",
                    "manufacturer_data",
                    "service_data",
                    "tx_power",
                }
            )
        else:
            unused = self._unused_fields(set())

        if unused:
            unused_list = ", ".join(sorted(unused))
            warnings.warn(
                f"Advertisement fields not used on {system}: {unused_list}",
                RuntimeWarning,
            )

    def _unused_fields(self, used: set) -> set:
        """
        Return the provided field names that are not in the OS-used set.
        """
        provided = {
            "local_name": self.local_name is not None,
            "service_uuids": self.service_uuids is not None,
            "manufacturer_data": self.manufacturer_data is not None,
            "service_data": self.service_data is not None,
            "is_connectable": self.is_connectable is not None,
            "is_discoverable": self.is_discoverable is not None,
            "tx_power": self.tx_power is not None,
        }
        return {
            name for name, present in provided.items() if present and name not in used
        }
