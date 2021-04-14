
"""
Example for a BLE 4.0 Server
"""

import logging
import asyncio
import threading

from typing import Any


from bless import (
        BlessServer,
        BlessGATTCharacteristic,
        GattCharacteristicsFlags,
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
        logger.debug("NICE")
        trigger.set()


async def run(loop):
    trigger.clear()
    # Instantiate the server
    my_service_name = "Test Service"
    server = BlessServer(name=my_service_name, loop=loop)
    server.read_request_func = read_request
    server.write_request_func = write_request

    # Add Service
    my_service_uuid = "A07498CA-AD5B-474E-940D-16F1FBE7E8CD"
    await server.add_new_service(my_service_uuid)

    # Add a Characteristic to the service
    my_char_uuid = "51FF12BB-3ED8-46E5-B4F9-D64E2FEC021B"
    char_flags = (
            GattCharacteristicsFlags.read |
            GattCharacteristicsFlags.write |
            GattCharacteristicsFlags.indicate
            )
    permissions = (
            GATTAttributePermissions.readable |
            GATTAttributePermissions.writeable
            )
    await server.add_new_characteristic(
            my_service_uuid,
            my_char_uuid,
            char_flags.value,
            None,
            permissions.value)

    logger.debug(
            server.services[my_service_uuid].get_characteristic(
                my_char_uuid.lower()
                )
            )
    await server.start()
    logger.debug("Advertising")
    logger.info(f"Write '0xF' to the advertised characteristic: {my_char_uuid}")
    trigger.wait()
    await asyncio.sleep(2)
    logger.debug("Updating")
    server.services[my_service_uuid].characteristics[0].value = b'WOW'
    server.update_value(
            my_service_uuid, "51FF12BB-3ED8-46E5-B4F9-D64E2FEC021B"
            )
    await asyncio.sleep(5)
    await server.stop()

loop = asyncio.get_event_loop()
loop.run_until_complete(run(loop))
