import bleak.backends.bluezdbus.defs as defs  # type: ignore

from typing import Dict, Optional, cast

from dbus_next.aio import MessageBus, ProxyObject, ProxyInterface  # type: ignore
from dbus_next.introspection import Node  # type: ignore


async def find_adapter(bus: MessageBus) -> Optional[str]:
    """
    Returns the first object within the bluez service that has a GattManager1
    interface

    Parameters
    ----------
    bus : MessageBus
        The currently connected message bus to communicate with BlueZ

    Returns
    -------
    Optional[str]
        The name of the adapter interface on the dbus.
        None if it does not find an adapter
    """
    bluez_node: Node = await bus.introspect(defs.BLUEZ_SERVICE, "/")
    bluez_obj: ProxyObject = bus.get_proxy_object(defs.BLUEZ_SERVICE, "/", bluez_node)
    interface: ProxyInterface = bluez_obj.get_interface(
        defs.OBJECT_MANAGER_INTERFACE
    )
    bt_objects: Dict = await interface.call_get_managed_objects()  # type: ignore

    for objs, props in bt_objects.items():
        if defs.GATT_MANAGER_INTERFACE in props.keys():
            return objs

    return None


async def get_adapter(bus: MessageBus) -> Optional[ProxyObject]:
    """
    Gets the bluetooth adapter

    Parameters
    ----------
    bus : MessageBus
        The connected DBus object

    Returns
    -------
    Optional[ProxyObject]
        The adapter object
        None if not found
    """
    oadapter_path: Optional[str] = await find_adapter(bus)
    if oadapter_path is None:
        return None

    adapter_path: str = cast(str, oadapter_path)
    adapter_node: Node = await bus.introspect(defs.BLUEZ_SERVICE, adapter_path)
    adapter_obj: ProxyObject = bus.get_proxy_object(
        defs.BLUEZ_SERVICE, adapter_path, adapter_node
    )
    return adapter_obj
