#!/bin/bash
# Install distutils
pip install setuptools
# Install the dependencies
pip install --target . --upgrade -r requirements.txt
