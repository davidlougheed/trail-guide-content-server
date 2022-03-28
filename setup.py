#!/usr/bin/env python
from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="trail_guide_content_server",
    version="0.6.0",

    python_requires="~=3.9",
    install_requires=[
        "click>=8.1.0,<8.2",
        "Flask>=2.0.3,<2.1",
        "Flask-Cors>=3.0.10,<3.1",
        "jsonschema>=4.4.0,<4.5",
        "PyJWT[crypto]>=2.3.0,<2.4",
        "python-dotenv>=0.20.0,<0.21",
        "qrcode[pil]>=7.3.0,<8",
        "Werkzeug>=2.1.0,<2.2",
    ],

    description="A server for storing content for a trail guide app.",
    long_description=long_description,
    long_description_content_type="text/markdown",

    url="https://github.com/davidlougheed/trail-guide-content-server",
    license="GPLv3",
    classifiers=[
        "Programming Language :: Python :: 3 :: Only",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],

    author="David Lougheed",
    author_email="david.lougheed@gmail.com",

    packages=find_packages(exclude="tests"),
    include_package_data=True,

    test_suite="tests"
)
