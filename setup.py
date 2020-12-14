import setuptools  # type: ignore

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="bless",
    version="0.1.0",
    author="Kevin Davis",
    author_email="kevincarrolldavis@gmail.com",
    description="A Bluetooth Low Energy Server supplement to Bleak",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kevincar/bless",
    packages=setuptools.find_packages(),
    install_requires=[
        "bleak"
        ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
