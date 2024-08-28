#!/bin/bash

set -e && [[ "$DEBUG" == 'true' ]] && set -x

RED="\033[0;31m"
GREEN="\033[0;32m"
NC="\033[00m"

empty_files_found=""

for file in $(git ls-files)
do
  if [[ -f "$file" && ! -s "$file" ]]; then
    empty_files_found="yes"
    printf "%b%s is empty!\n%b" "$RED" "$file" "$NC"
  fi
done

if [[ $empty_files_found == "yes" ]]; then
  printf "%bEmpty files detected!\n%b" "$RED" "$NC"
  exit 1;
fi

printf "%bNo empty files detected.\n%b" "$GREEN" "$NC"
