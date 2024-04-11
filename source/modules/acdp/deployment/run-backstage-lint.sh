#!/bin/bash

set -e && [[ "$DEBUG" == 'true' ]] && set -x

# CD into one level above the deployment dir where this script is located
# module_root_dir_absolute_path="$PWD"
cd "$(dirname "$0")"
cd ../backstage

yarn tsc:full
