#!/usr/bin/env python

from ez_setup import use_setuptools
use_setuptools()

from setuptools import setup

setup(
    name = "Burton",
    version = "1.0.1",
    description = "Localization scripts for Extensis",
    author = "Michael Buckley",
    author_email = "mbuckley@extensis.com",
    packages = [ "burton",  "burton.database", "burton.vcs", "burton.parser", "burton.translation" ],
    install_requires = [
        "chardet", "lxml"
    ],
    extras_require = {
        "test" : [ "coverage", "mock", "nose", "textfixtures" ]
    },
    include_package_data = True,
)
