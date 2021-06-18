# Bless

[![Build, Lint, and
Test](https://github.com/kevincar/bless/actions/workflows/build-and-test.yml/badge.svg)
](https://github.com/kevincar/bless/actions/workflows/build-and-test.yml)
[![PyPI version](https://badge.fury.io/py/bless.svg)](https://badge.fury.io/py/bless)
![PyPI - Downloads](https://img.shields.io/pypi/dm/bless)
[![Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Bless is an acronym for Bluetooth Low Energy (BLE) Server Supplement.

Bless provides an OS-independent python package for creating a BLE Generic
Attribute Profile (GATT) server to broadcast user-defined services and
characteristics. This is particularly useful when prototyping and testing
servers on different devices with the goal of ensuring that expected behavior
matches across all systems.

Bless's code roughly follows a similar style to
[Bleak](https://github.com/hbldh/bleak) in order to ease development of client
and server programs.

# Installation

```bash
pip install bless
```

# Features

Bless enables reading, writing, and notifying of BLE characteristic values.
Developers can provide callback functions to manipulate data that is sent out
for reading or delivered for writing prior to processing the underlying
commands.

# Examples

See example code for setting up a BLE server where read and write
characteristic can be be probed by BLE clients (central devices)

[Basic Server
Example](https://github.com/kevincar/bless/blob/master/examples/server.py)

[GATT Tree Server
Example](https://github.com/kevincar/bless/blob/master/examples/gattserver.py)
