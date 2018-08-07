#!/usr/bin/env bash

setup_command=${1:-install}
echo Installing using command: setup.py $setup_command

cd mongo && 
    python setup.py $setup_command && 
    cd ../backend && 
    python setup.py $setup_command && 
    cd ../frontend && 
    python setup.py $setup_command && 
    echo "done"