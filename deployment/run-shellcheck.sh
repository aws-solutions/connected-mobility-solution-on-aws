#!/bin/bash

set -e && [[ "$DEBUG" == 'true' ]] && set -x

RED="\033[0;31m"
NC="\033[00m"

if command -v "shellcheck" >/dev/null 2>&1; then
    shellcheck "$@"
else
    printf "%bYour system does not have shellcheck, instructions are here https://github.com/koalaman/shellcheck#installing\n%b" "${RED}" "${NC}" && exit 1
fi
