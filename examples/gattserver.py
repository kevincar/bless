
"""
Example for a BLE 4.0 Server using a GATT dictionary of services and
characteristics
"""

import logging
import asyncio
import threading

from typing import Any, Dict

from bless import (  # type: ignore
        BlessServer,
        BlessGATTCharacteristic,
        GATTCharacteristicProperties,
        GATTAttributePermissions
        )

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(name=__name__)
trigger: threading.Event = threading.Event()


def read_request(
        characteristic: BlessGATTCharacteristic,
        **kwargs
        ) -> bytearray:
    logger.debug(f"Reading {characteristic.value}")
    return characteristic.value


def write_request(
        characteristic: BlessGATTCharacteristic,
        value: Any,
        **kwargs
        ):
    characteristic.value = value
    logger.debug(f"Char value set to {characteristic.value}")
    if characteristic.value == b'\x0f':
        logger.debug("Nice")
        trigger.set()


async def run(loop):
    trigger.clear()

    # Instantiate the server
    gatt: Dict = {
            "A07498CA-AD5B-474E-940D-16F1FBE7E8CD": {
                "51FF12BB-3ED8-46E5-B4F9-D64E2FEC021B": {
                    "Properties": (GATTCharacteristicProperties.read |
                                   GATTCharacteristicProperties.write |
                                   GATTCharacteristicProperties.indicate),
                    "Permissions": (GATTAttributePermissions.readable |
                                    GATTAttributePermissions.writeable),
                    "Value": None
                    }
                }
            }
    my_service_name = "Test Service"
    server = BlessServer(name=my_service_name, loop=loop)
    server.read_request_func = read_request
    server.write_request_func = write_request

    await server.add_gatt(gatt)
    await server.start()
    logger.debug(server.get_characteristic(
        "51FF12BB-3ED8-46E5-B4F9-D64E2FEC021B"))
    logger.debug("Advertising")
    logger.info("Write '0xF' to the advertised characteristic: " +
                "51FF12BB-3ED8-46E5-B4F9-D64E2FEC021B")
    trigger.wait()
    await asyncio.sleep(2)
    logger.debug("Updating")
    server.get_characteristic("51FF12BB-3ED8-46E5-B4F9-D64E2FEC021B").value = (
            bytearray(b"i")
            )
    server.update_value(
            "A07498CA-AD5B-474E-940D-16F1FBE7E8CD",
            "51FF12BB-3ED8-46E5-B4F9-D64E2FEC021B"
            )
    await asyncio.sleep(5)
    await server.stop()

loop = asyncio.get_event_loop()
loop.run_until_complete(run(loop))
