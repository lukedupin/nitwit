#!/usr/bin/bash

rm -rf build dist caterpillar_api.egg-info

python3 setup.py sdist bdist_wheel

twine upload dist/*
