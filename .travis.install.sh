#!/bin/bash

deps=( "." "mypy" "sphinx")

for pkg in "${deps[@]}"
do
    pip3 install --user -U --progress-bar off $pkg
done
