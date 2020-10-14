from enum import Flag


class GattCharacteristicsFlags(Flag):
    broadcast = 0x0001
    read = 0x0002
    write_without_response = 0x0004
    write = 0x0008
    notify = 0x0010
    indicate = 0x0020
    authenticated_signed_writes = 0x0040
    extended_properties = 0x0080
    reliable_write = 0x0100
    writable_auxiliaries = 0x0200
