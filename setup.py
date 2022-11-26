#!/usr/bin/env python
from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("./trail_guide_content_server/VERSION", "r") as vf:
    version = vf.read().strip()

setup(
    name="trail_guide_content_server",
    version=version,

    python_requires="~=3.10",
    install_requires=[
        "click>=8.1.3,<8.2",
        "Flask>=2.2.2,<2.3",
        "Flask-Cors>=3.0.10,<3.1",
        "jsonschema>=4.17.1,<4.18",
        "PyJWT[crypto]>=2.6.0,<2.7",
        "python-dotenv>=0.21.0,<0.22",
        "qrcode[pil]>=7.3.0,<8",
        "requests>=2.28.1,<2.29",
        "Werkzeug>=2.2.2,<2.3",
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
