#!/bin/bash

if command -v "shellcheck" >/dev/null 2>&1; then
    shellcheck "$@"
else
    echo 'Your system does not have shellcheck, instructions are here https://github.com/koalaman/shellcheck#installing'
    exit 1
fi
