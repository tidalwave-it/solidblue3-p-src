#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name="solidblue3",
    version="1.0",  # FIXME __version__
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    package_data={"solidblue3": ["resources/**/*"]},
)