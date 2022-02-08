#!/usr/bin/python

import pathlib
import sys

import setuptools

# Get root directory.
root_dir = pathlib.Path(__file__).parent.resolve()

# Add root directory to PYTHONPATH.
sys.path.insert(0, root_dir)

# Get source directory.
src_dir = root_dir / "kinectacq"

# Find packages within source directory.

# Read dependencies for documentation generation.
docs_requirements_file = root_dir / "docs" / "requirements.txt"
docs_requirements = docs_requirements_file.read_text().splitlines()

setuptools.setup(
    name="kinectacq",
    version="0.0.9",
    description="A Python package test2",
    long_description="",
    url="",
    author="",
    author_email="",
    license="MIT",
    classifiers=[],
    packages=setuptools.find_packages(),
    install_requires=["numpy>=1.20", "click"],
    extras_require={
        # "test": ["pytest", "coverage"],
        # "lint": ["pylama", "isort", "mypy"],
        "docs": docs_requirements,
    },
    python_requires=">=3.7",
    include_package_data=True,
    zip_safe=False,
)
