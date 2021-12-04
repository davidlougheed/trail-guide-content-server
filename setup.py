#!/usr/bin/env python
from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="trail_guide_content_server",
    version="0.1.3",

    python_requires="~=3.9",
    install_requires=[
        "Flask>=2.0.2,<2.1",
        "Flask-Cors>=3.0.10,<3.1",
        "jsonschema>=4.2.1,<4.3",
        "PyJWT[crypto]>=2.3.0,<2.4",
        "python-dotenv>=0.19.2,<0.20",
        "Werkzeug>=2.0.2,<2.1",
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
