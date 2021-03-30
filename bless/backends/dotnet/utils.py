import asyncio
from typing import Any, Dict

from Windows.Foundation import IAsyncOperation  # type: ignore
from bleak.backends.dotnet.utils import wrap_IAsyncOperation  # type: ignore


async def async_wrap(ref_obj: Dict, ret_type: Any, fn: Any, *args):
    """
    This function is called by sync_async_wrap to create a synchronous wrapper
    for the asynchronous wrapper. This may temporarily introduce some
    redundancy but is required for dotnet server read and write requests

    Parameters
    ----------
    ref_obj : Dict
        A dictionary whose key 'value' will be set to the value to be obtained
        synchronously
    ret_type: Any
        The value type of the object that will be set to ref_obj['value']
    fn : Any
        The function whose return value is the value to be set to
        ref_obj['value']
    """
    # Main Operation
    op: IAsyncOperation = IAsyncOperation[ret_type](fn(*args))

    # Wrap and await
    ref_obj["value"] = await wrap_IAsyncOperation(op, ret_type)


def sync_async_wrap(ret_type: Any, fn: Any, *args) -> Any:
    """
    Converts an asynchronous operation to a synchronous one

    Parameters
    ----------
    ret_type : Any
        The type of the variable expected on return
    fn : Any
        An asynchronous function to call whose return value is a type equal to
        that of ret_type
    """
    reference_obj: Dict = {}
    asyncio.new_event_loop().run_until_complete(
        async_wrap(reference_obj, ret_type, fn, *args)
    )
    return reference_obj["value"]
