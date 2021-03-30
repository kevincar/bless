from enum import Enum


class CBATTError(Enum):
    """CBATTError enumeration"""

    Success = 0x0
    InvalidHandle = 0x1
    ReadNotPermitted = 0x2
    WriteNotPermitted = 0x3
    InvalidPdu = 0x4
    InsufficientAuthentication = 0x5
    RequestNotSupported = 0x6
    InvalidOffset = 0x7
    InsufficientAuthorization = 0x8
    PrepareQueueFull = 0x9
    AttributeNotFound = 0xA
    AttributeNotLong = 0xB
    InsufficientEncryptionKeySize = 0xC
    InvalidAttributeValueLength = 0xD
    UnlikelyError = 0xE
    InsufficientEncryption = 0xF
    UnsupportedGroupType = 0x10
    InsufficientResources = 0x11
