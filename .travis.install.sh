#!/bin/bash

deps=( "." "mypy" "sphinx")

for pkg in "${deps[@]}"
do
    pip3 install -U --progress-bar off $pkg
done
