from enum import Flag


class GATTAttributePermissions(Flag):
    readable = 0x1
    writeable = 0x2
    read_encryption_required = 0x4
    write_encryption_required = 0x8
