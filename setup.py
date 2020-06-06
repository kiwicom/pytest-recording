#!/usr/bin/env python
# -*- coding: utf-8 -*-

import codecs
import os
import sys

from setuptools import find_packages, setup

install_requires = ["vcrpy>=2.0.1", "attrs"]

if sys.version_info[0] == 2:
    install_requires.append("pytest>=3.5.0,<5.0")
else:
    install_requires.append("pytest>=3.5.0")


def read(fname):
    file_path = os.path.join(os.path.dirname(__file__), fname)
    return codecs.open(file_path, encoding="utf-8").read()


setup(
    name="pytest-recording",
    version="0.8.0",
    author="Dmitry Dygalo",
    author_email="dmitry.dygalo@kiwi.com",
    maintainer="Dmitry Dygalo",
    maintainer_email="dmitry.dygalo@kiwi.com",
    url="https://github.com/kiwicom/pytest-recording",
    license="MIT",
    description="A pytest plugin that allows to record network interactions via VCR.py",
    long_description=read("README.rst"),
    long_description_content_type="text/x-rst",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*",
    install_requires=install_requires,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Framework :: Pytest",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Operating System :: OS Independent",
    ],
    entry_points={"pytest11": ["recording = pytest_recording.plugin"]},
)
