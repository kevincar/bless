import sys
import uuid
import pytest
import threading
import asyncio
import aioconsole  # type: ignore

import numpy as np  # type: ignore

from uuid import UUID
from concurrent.futures import ThreadPoolExecutor

if sys.platform.lower() != "win32":
    pytest.skip("Only for windows", allow_module_level=True)

from typing import List, Any  # noqa: E402

hardware_only = pytest.mark.skipif("os.environ.get('TEST_HARDWARE') is None")

from bless.backends.characteristic import (  # type: ignore # noqa: E402
    GATTCharacteristicProperties,
    GATTAttributePermissions,
)

if sys.version_info >= (3, 12):
    from winrt.windows.foundation import Deferral  # type: ignore # noqa: E402 E501
    from winrt.windows.storage.streams import DataReader, DataWriter  # type: ignore # noqa: E402 E501
    from winrt.windows.devices.bluetooth.genericattributeprofile import (  # type: ignore # noqa: E402 F401 E501
        GattWriteOption,
        GattServiceProviderResult,
        GattServiceProvider,
        GattLocalService,
        GattLocalCharacteristicResult,
        GattLocalCharacteristic,
        GattLocalCharacteristicParameters,
        GattServiceProviderAdvertisingParameters,
        GattServiceProviderAdvertisementStatusChangedEventArgs,
        GattReadRequestedEventArgs,
        GattReadRequest,
        GattWriteRequestedEventArgs,
        GattWriteRequest,
        GattSubscribedClient,
    )
else:
    from bleak_winrt.windows.foundation import Deferral  # type: ignore # noqa: E402 E501

    from bleak_winrt.windows.storage.streams import DataReader, DataWriter  # type: ignore # noqa: E402 E501

    from bleak_winrt.windows.devices.bluetooth.genericattributeprofile import (  # type: ignore # noqa: E402 F401 E501
        GattWriteOption,
        GattServiceProviderResult,
        GattServiceProvider,
        GattLocalService,
        GattLocalCharacteristicResult,
        GattLocalCharacteristic,
        GattLocalCharacteristicParameters,
        GattServiceProviderAdvertisingParameters,
        GattServiceProviderAdvertisementStatusChangedEventArgs,
        GattReadRequestedEventArgs,
        GattReadRequest,
        GattWriteRequestedEventArgs,
        GattWriteRequest,
        GattSubscribedClient,
    )


@hardware_only
class TestServiceProvider:
    """
    Test
    """

    hex_words: List[str] = [
        "DEAD",
        "FACE",
        "BABE",
        "CAFE",
        "FADE",
        "BAD",
        "DAD",
        "ACE",
        "BED",
    ]

    val: bytearray = bytearray([0])

    _subscribed_clients: List = []

    def input(self, msg: str):
        with ThreadPoolExecutor(max_workers=1) as executor:
            ftr = executor.submit(input, msg)
        return ftr.result()

    @pytest.mark.asyncio
    async def test_init(self):

        start_event: threading.Event = threading.Event()

        def advertisement_status_changed(
            sender: GattServiceProvider,
            args: GattServiceProviderAdvertisementStatusChangedEventArgs,
        ):
            print(f"Advertisement status has changed: {args.status}")
            if args.status == 2:
                start_event.set()

        def read(
                sender: GattLocalCharacteristic,
                args: GattReadRequestedEventArgs):
            print("Read")
            deferral: Deferral = args.get_deferral()
            value = self.val
            writer: DataWriter = DataWriter()
            writer.write_bytes(value)
            request: GattReadRequest

            async def f():
                nonlocal request
                nonlocal args
                request = await args.get_request_async()
            asyncio.run(f())
            request.respond_with_value(writer.detach_buffer())
            deferral.complete()

        def write(
                sender: GattLocalCharacteristic,
                args: GattWriteRequestedEventArgs):
            print("WRITE")
            deferral: Deferral = args.get_deferral()
            request: GattWriteRequest

            async def f():
                nonlocal args
                nonlocal request
                request = await args.get_request_async()
            asyncio.run(f())
            reader: DataReader = DataReader.from_buffer(request.value)
            n_bytes: int = reader.unconsumed_buffer_length
            value: bytearray = bytearray()
            for n in range(0, n_bytes):
                next_byte: int = reader.read_byte()
                value.append(next_byte)
            self.val = value

            if request.option == GattWriteOption.WRITE_WITH_RESPONSE:
                request.respond()

            deferral.complete()

        def subscribe(sender: GattLocalCharacteristic, args: Any):
            self._subscribed_clients = list(sender.subscribed_clients)

        # Create service
        service_uuid: UUID = uuid.uuid4()
        service_provider_result: GattServiceProviderResult = (
            await GattServiceProvider.create_async(service_uuid)
        )
        service_provider: GattServiceProvider = (
                service_provider_result.service_provider
                )
        service_provider.add_advertisement_status_changed(advertisement_status_changed)

        new_service: GattLocalService = service_provider.service

        # Add a characteristic
        char_uuid: UUID = uuid.uuid4()

        properties: GATTCharacteristicProperties = (
            GATTCharacteristicProperties.read
            | GATTCharacteristicProperties.write
            | GATTCharacteristicProperties.notify
        )

        permissions: GATTAttributePermissions = (
            GATTAttributePermissions.readable |
            GATTAttributePermissions.writeable
        )

        read_parameters: GattLocalCharacteristicParameters = (
            GattLocalCharacteristicParameters()
        )
        read_parameters.characteristic_properties = properties.value
        read_parameters.read_protection_level = permissions.value

        characteristic_result: GattLocalCharacteristicResult = (
            await new_service.create_characteristic_async(char_uuid, read_parameters)
        )
        new_char: GattLocalCharacteristic = characteristic_result.characteristic
        new_char.add_read_requested(read)
        new_char.add_write_requested(write)
        new_char.add_subscribed_clients_changed(subscribe)

        # Ensure we're not advertising
        assert service_provider.advertisement_status != 2

        # Advertise
        adv_parameters: GattServiceProviderAdvertisingParameters = (
            GattServiceProviderAdvertisingParameters()
        )
        adv_parameters.is_discoverable = True
        adv_parameters.is_connectable = True

        service_provider.start_advertising(adv_parameters)

        # Check
        start_event.wait()
        assert service_provider.advertisement_status == 2

        # We shouldn't be connected
        assert len(self._subscribed_clients) < 1

        print(
            "\nPlease connect now"
            + "and subscribe to the characteristic {}...".format(char_uuid)
        )
        await aioconsole.ainput("Press enter when ready...")

        assert len(self._subscribed_clients) > 0

        # Read test
        rng: np.random._generator.Generator = np.random.default_rng()
        hex_val: str = "".join(rng.choice(self.hex_words, 2, replace=False))
        self.val = bytearray(
            int(f"0x{hex_val}", 16).to_bytes(
                length=int(np.ceil(len(hex_val) / 2)), byteorder="big"
            )
        )

        print("Trigger a read and enter the hex value you see below")
        entered_value = await aioconsole.ainput("Value: ")
        assert entered_value == hex_val

        # Write test
        hex_val = "".join(rng.choice(self.hex_words, 2, replace=False))
        print(f"Set the characteristic to the following: {hex_val}")
        await aioconsole.ainput("Press enter when ready...")
        str_val: str = "".join([hex(x)[2:] for x in self.val]).upper()
        assert str_val == hex_val

        # Notify test
        hex_val = "".join(rng.choice(self.hex_words, 2, replace=False))
        self.val = bytearray(
            int(f"0x{hex_val}", 16).to_bytes(
                length=int(np.ceil(len(hex_val) / 2)), byteorder="big"
            )
        )

        print("A new value will be sent")
        await aioconsole.ainput("Press enter to receive the new value...")

        writer: DataWriter = DataWriter()
        writer.write_bytes(self.val)
        await new_char.notify_value_async(writer.detach_buffer())

        new_value: str = await aioconsole.ainput("Enter the New value: ")
        assert new_value == hex_val

        # unsubscribe
        print("Unsubscribe from the characteristic")
        await aioconsole.ainput("Press enter when ready...")
        assert len(self._subscribed_clients) < 1

        # Stop Advertising
        service_provider.stop_advertising()

        # There are some cases where calls to `StopAdvertising` does not update
        # the `AdvertisementStatus`
        # assert service_provider.advertisement_status != 2
