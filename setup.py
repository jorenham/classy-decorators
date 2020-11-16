from pathlib import Path

from setuptools import find_packages, setup

_BASE_PATH = Path(__file__).parent
_VERSION_PATH = _BASE_PATH / "VERSION"

NAME = "Classy Decorators"
DESCRIPTION = (
    "Hassle-free creation of decorators for functions and methods, OO-style."
)
URL = "https://github.com/jorenham/classy-decorators/"
AUTHOR = "Joren Hammudoglu"

REQUIRES_PYTHON = ">=3.8.0"
VERSION = _VERSION_PATH.read_text().strip()
REQUIREMENTS = []

setup(
    name=NAME,
    description=DESCRIPTION,
    author=AUTHOR,
    url=URL,
    version=VERSION,
    install_requires=REQUIREMENTS,
    packages=find_packages(exclude=["tests"]),
    long_description="Utility package for creating class-bassed decorators.",
    classifiers=[
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: POSIX",
    ],
)
