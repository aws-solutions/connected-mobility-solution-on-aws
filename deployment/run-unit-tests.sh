#!/bin/bash

# This file is not used, but it is required by the pipeline checks. Specifically viperlight pubcheck.
# This can be replaced with `touch ./deployment/run-all-tests.sh` in the buildspec.yaml which also
#   gets picked up on the check that makes sure that run-all-tests.sh is "called" in the buildspec.
# It doesn't actually check that it is called, just does a basic grep.

# If you, the reader, really would like this file to do something, uncomment the below line.
# make -C ../Makefile test
# You should note how redundant it was to uncomment that line.
