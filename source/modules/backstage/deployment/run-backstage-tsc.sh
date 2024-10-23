#!/bin/bash

set -e && [[ "$DEBUG" == 'true' ]] && set -x

# CD into one level above the deployment dir where this script is located
cd "$(dirname "$0")"/..

yarn tsc:full
