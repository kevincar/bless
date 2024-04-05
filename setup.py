import setuptools  # type: ignore

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="bless",
    version="0.2.6",
    author="Kevin Davis",
    author_email="kevincarrolldavis@gmail.com",
    description="A Bluetooth Low Energy Server supplement to Bleak",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kevincar/bless",
    package_data={"bless": ["py.typed"]},
    packages=setuptools.find_packages(exclude=("test", "examples")),
    include_package_data=True,
    install_requires=[
        "bleak",
        "pywin32;platform_system=='Windows'",
        "dbus_next;platform_system=='Linux'",
        "pysetupdi @ git+https://github.com/gwangyi/pysetupdi#egg=pysetupdi;platform_system=='Windows'",  # noqa: E501
        'bleak-winrt>=1.2.0; platform_system=="Windows" and python_version<"3.12"',
        'winrt-Windows.Devices.Bluetooth==2.0.0b1; platform_system=="Windows" and python_version>="3.12"',
        'winrt-Windows.Devices.Bluetooth.Advertisement==2.0.0b1; platform_system=="Windows" and python_version>="3.12"',
        'winrt-Windows.Devices.Bluetooth.GenericAttributeProfile==2.0.0b1; platform_system=="Windows" and python_version>="3.12"',
        'winrt-Windows.Devices.Enumeration==2.0.0b1; platform_system=="Windows" and python_version>="3.12"',
        'winrt-Windows.Foundation==2.0.0b1; platform_system=="Windows" and python_version>="3.12"',
        'winrt-Windows.Foundation.Collections==2.0.0b1; platform_system=="Windows" and python_version>="3.12"',
        'winrt-Windows.Storage.Streams==2.0.0b1; platform_system=="Windows" and python_version>="3.12"',
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
