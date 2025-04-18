#!/bin/bash

set -e && [[ "$DEBUG" == 'true' ]] && set -x

generate_report=true

while [[ $# -gt 0 ]]; do
  case $1 in
  -r | --no-report)
    unset generate_report
    shift
    ;;
  -s | --snapshot-update)
    snapshot_update=true
    shift
    ;;
  *)
    shift
    ;;
  esac
done

#TEMP: Workaround for HEAP OUT OF MEMORY
export NODE_OPTIONS=--max-old-space-size=8192

# Get reference for all important folders and files
project_dir="$(dirname "$(dirname "$(realpath "$0")")")"
source_dir="$project_dir/source"
smithy_dir="$source_dir/smithy"
frontend_dir="$source_dir/frontend"
fleet_management_api_dir="$source_dir/handlers/fleet_management"

cd "$smithy_dir"
smithy build
cd "$project_dir"

yarn --cwd "$frontend_dir" run build:smithy-codegen
yarn --cwd "$frontend_dir" install --immutable --refresh-lockfile
yarn --cwd "$frontend_dir" build
yarn --cwd "$fleet_management_api_dir" run build:smithy-codegen

root_dir="$(dirname "$(dirname "$(dirname "$project_dir")")")"
module_name="$(basename "$project_dir")"
python_coverage_report="$root_dir/coverage-reports/$module_name-coverage.xml"

rm -f "$project_dir/.coverage"

# Run test on package and save results to coverage_report_path in xml format
pytest "$source_dir" \
  --cov="$source_dir" \
  --cov-report=term \
  --cov-config="$project_dir/pyproject.toml" \
  ${generate_report:+--cov-report=xml:$python_coverage_report} \
  ${snapshot_update:+--snapshot-update}

yarn --cwd "$fleet_management_api_dir" test

# Only perform the sed transformation if a report was generated, to guarantee the coveragereport file exists
if [ "$generate_report" = true ]; then
  # Linux and MacOS have different ways of calling the sed command for in-place editing. MacOS takes a mandatory argument for the -i flag whereas linux does not.
  sedi=(-i)
  if [[ "$OSTYPE" == "darwin"* ]]; then
    sedi=(-i "")
  fi

  # The pytest coverage report generated includes the absolute path to the root directory.
  # Sonarqube requires a path that is instead relative to the root directory.
  # To accomplish this, we remove the absolute path portion of the root directory.
  sed "${sedi[@]}" -e "s,<source>$root_dir/,<source>,g" "$python_coverage_report"
fi
