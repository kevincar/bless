import bleak.backends.bluezdbus.defs as defs  # type: ignore

from typing import Dict, List, Optional

from dbus_next.aio import MessageBus, ProxyObject, ProxyInterface  # type: ignore
from dbus_next.introspection import Node  # type: ignore


async def list_adapters(bus: MessageBus) -> List[str]:
    """
    Returns a list of strings that represent host-controller interfaces for
    bluetooth

    Parameters
    ----------
    bus : MessageBux
        The currently connected message bus to communicate with BlueZ

    Returns
    -------
    List[str]
        A list of adapter interfaces on the dbus
    """
    bluez_node: Node = await bus.introspect(defs.BLUEZ_SERVICE, "/")
    bluez_obj: ProxyObject = bus.get_proxy_object(defs.BLUEZ_SERVICE, "/", bluez_node)
    interface: ProxyInterface = bluez_obj.get_interface(defs.OBJECT_MANAGER_INTERFACE)
    bt_objects: Dict = await interface.call_get_managed_objects()  # type: ignore

    adapters: List[str] = [
        objs
        for objs, props in bt_objects.items()
        if defs.GATT_MANAGER_INTERFACE in props.keys()
    ]
    return adapters


async def find_adapter(bus: MessageBus, adapter: str = "hci0") -> str:
    """
    Returns the first object within the bluez service that has a GattManager1
    interface

    Parameters
    ----------
    bus : MessageBus
        The currently connected message bus to communicate with BlueZ

    adapter : str
        The adapter to find. Default is 'hci0'

    Returns
    -------
    str
        The dbus path to the adapter
    """
    adapter_strs: List[str] = await list_adapters(bus)
    found_adapter: List[str] = [a for a in adapter_strs if adapter in a]
    if len(found_adapter) > 0:
        return found_adapter[0]
    raise Exception(f"No adapter named {adapter} found")


async def get_adapter(bus: MessageBus, adapter: Optional[str] = None) -> ProxyObject:
    """
    Gets the bluetooth adapter specified by adapter or the default if adapter
    is None

    Parameters
    ----------
    bus : MessageBus
        The connected DBus object
    adapter: Optional[str]
        A string that points to the HCI adapter

    Returns
    -------
    ProxyObject
        The adapter object
    """
    adapter_path: str = await find_adapter(
        bus, adapter if adapter is not None else "hci0"
    )
    adapter_node: Node = await bus.introspect(defs.BLUEZ_SERVICE, adapter_path)
    adapter_obj: ProxyObject = bus.get_proxy_object(
        defs.BLUEZ_SERVICE, adapter_path, adapter_node
    )
    return adapter_obj
