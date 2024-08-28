#!/bin/bash

set -e && [[ "$DEBUG" == 'true' ]] && set -x

generate_report=true

while [[ $# -gt 0 ]]
do
  case $1 in
    -r|--no-report)
        unset generate_report
        shift
        ;;
    -s|--snapshot-update)
        snapshot_update=true
        shift
        ;;
    *)
        shift
        ;;
  esac
done

# Get reference for all important folders and files
project_dir="$(dirname "$(dirname "$(realpath "$0")")")"
source_dir="$project_dir/source"
console_dir="$source_dir/console"

root_dir="$(dirname "$(dirname "$(dirname "$project_dir")")")"
module_name="$(basename "$project_dir")"
python_coverage_report="$root_dir/coverage-reports/$module_name-coverage.xml"

rm -f "$project_dir/.coverage"

# <=====UNIQUE TO VEHICLE SIMULATOR=====>
# Run tests for vehicle simulator front-end console application. This must be done before python testing
# so the cloudformation distribution can find the front-end asset.
npm run build --prefix="$console_dir"
npm run test --prefix="$console_dir"

rm -rf "$console_dir/coverage/lcov-report"
# <=====UNIQUE TO VEHICLE SIMULATOR=====>

# Run test on package and save results to coverage_report_path in xml format
pytest "$source_dir" \
  --cov="$source_dir"  \
  --cov-report=term \
  --cov-config="$project_dir/pyproject.toml" \
  ${generate_report:+--cov-report=xml:$python_coverage_report} \
  ${snapshot_update:+--snapshot-update}

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
