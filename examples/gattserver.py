"""
Example for a BLE 4.0 Server using a GATT dictionary of services and
characteristics
"""

import asyncio
import logging
import sys
import threading

from typing import Any, Dict, Union

from bless import (  # type: ignore
    BlessServer,
    BlessGATTCharacteristic,
    GATTCharacteristicProperties,
    GATTAttributePermissions,
    BlessGATTRequest,
    BlessGATTSession,
)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(name=__name__)

trigger: Union[asyncio.Event, threading.Event] = (
    threading.Event() if sys.platform in ["darwin", "win32"] else asyncio.Event()
)


def on_read(
    characteristic: BlessGATTCharacteristic, request: BlessGATTRequest
) -> bytearray:
    logger.debug(f"Reading {characteristic.value}")
    return characteristic.value


def on_write(
    characteristic: BlessGATTCharacteristic, value: Any, request: BlessGATTRequest
):
    characteristic.value = value
    logger.debug(f"Char value set to {characteristic.value}")
    if characteristic.value == b"\x0f":
        logger.debug("Nice")
        trigger.set()


def on_subscribe(characteristic: BlessGATTCharacteristic, session: BlessGATTSession):
    logger.debug(f"Subscribed to {characteristic.uuid}")


def on_unsubscribe(characteristic: BlessGATTCharacteristic, session: BlessGATTSession):
    logger.debug(f"Unsubscribed from {characteristic.uuid}")


# Characteristic-specific handlers
def inc(c: BlessGATTCharacteristic, req: BlessGATTRequest) -> bytearray:
    c.value = c.value if c.value is not None else bytearray("\x00")
    n: int = int.from_bytes(bytes(c.value))
    c.value = bytearray((n + 1).to_bytes())
    return c.value


async def run(loop):
    trigger.clear()

    # Instantiate the server
    gatt: Dict = {
        "A07498CA-AD5B-474E-940D-16F1FBE7E8CD": {
            "51FF12BB-3ED8-46E5-B4F9-D64E2FEC021B": {
                "Properties": (
                    GATTCharacteristicProperties.read
                    | GATTCharacteristicProperties.write
                    | GATTCharacteristicProperties.indicate
                ),
                "Permissions": (
                    GATTAttributePermissions.readable
                    | GATTAttributePermissions.writeable
                ),
                "Value": None,
            }
        },
        "5c339364-c7be-4f23-b666-a8ff73a6a86a": {
            "bfc0c92f-317d-4ba9-976b-cc11ce77b4ca": {
                "Properties": GATTCharacteristicProperties.read,
                "Permissions": GATTAttributePermissions.readable,
                "Value": None,
                "OnRead": inc,
            }
        },
    }
    my_service_name = "Test Service"
    server = BlessServer(
        name=my_service_name,
        loop=loop,
        on_read=on_read,
        on_write=on_write,
        on_subscribe=on_subscribe,
        on_unsubscribe=on_unsubscribe,
    )

    await server.add_gatt(gatt)
    await server.start()
    logger.debug(server.get_characteristic("51FF12BB-3ED8-46E5-B4F9-D64E2FEC021B"))
    logger.debug("Advertising")
    logger.info(
        "Write '0xF' to the advertised characteristic: "
        + "51FF12BB-3ED8-46E5-B4F9-D64E2FEC021B"
    )
    if isinstance(trigger, threading.Event):
        trigger.wait()
    else:
        await trigger.wait()
    logger.info("Triggered... Waiting 2 seconds")
    await asyncio.sleep(2)

    logger.debug("Updating characteristic")
    server.get_characteristic("51FF12BB-3ED8-46E5-B4F9-D64E2FEC021B").value = bytearray(
        b"i"
    )
    server.update_value(
        "A07498CA-AD5B-474E-940D-16F1FBE7E8CD", "51FF12BB-3ED8-46E5-B4F9-D64E2FEC021B"
    )
    await asyncio.sleep(5)
    await server.stop()


loop = asyncio.get_event_loop()
loop.run_until_complete(run(loop))
