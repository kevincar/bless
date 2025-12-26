Backends
========

Bless provides a thin, OS-specific backend layer under `bless/backends`. The
top-level `bless` package selects the backend based on the current platform.

.. toctree::
   :maxdepth: 2
   :caption: Backends:

   advertisement
   attribute
   characteristic
   descriptor
   service
   server
   bluezdbus/index
   corebluetooth/index
   winrt/index
