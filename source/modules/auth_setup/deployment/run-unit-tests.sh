#!/bin/bash

set -e && [[ "$DEBUG" == 'true' ]] && set -x

showHelp() {
cat << EOF
Usage: ./deployment/run-unit-tests.sh --help

Run unit tests in this module.

-r,   --no-report                       Don't generate the report, this is mainly used for pre-commit

-s,   --snapshot-update                 Update cdk snapshots

EOF
}

generate_report=true

for flag in "$@"
do
  case "$flag" in
    -h|--help)
        showHelp
        exit 0
        ;;
    -r|--no-report)
        unset generate_report
        ;;
    -s|--snapshot-update)
        snapshot_update=true
        ;;
    *)
        printf "Unrecognized flag %s." "${flag}"
        printf "Please use --help to see the list of supported flags. This script does not use any positional args.\n"
        printf "Exiting script with error code 1.\n\n"
        exit 1
        ;;
  esac
done

cd "$(dirname "$0")"/..

# Get reference for all important folders and files
project_dir="$PWD"
source_dir="$project_dir/source"
tests_dir="$source_dir/tests"
python_coverage_report="$source_dir/tests/coverage-reports/coverage.xml"

rm -f "$project_dir/.coverage"

# Run test on package and save results to coverage_report_path in xml format
pytest "$tests_dir" \
  --cov="$source_dir"  \
  --cov-report=term \
  --cov-config="$project_dir/pyproject.toml" \
  ${generate_report:+--cov-report=xml:$python_coverage_report} \
  ${snapshot_update:+--snapshot-update}

# Only perform the sed transformation if a report was generated, to guarantee the coveragereport file exists
if [ "$generate_report" = true ]
then
  # Linux and MacOS have different ways of calling the sed command for in-place editing.
  # MacOS takes a mandatory argument for the -i flag whereas linux does not.
  sedi=(-i)
  if [[ "$OSTYPE" == "darwin"* ]]; then
    sedi=(-i "")
  fi

  # The pytest coverage report generated includes the absolute path to the root directory.
  # Sonarqube requires a path that is instead relative to the root directory.
  # To accomplish this, we remove the absolute path portion of the root directory.
  repo_root="$(dirname "$(dirname "$(dirname "$project_dir")")")"
  sed "${sedi[@]}" -e "s,<source>$repo_root/,<source>,g" "$python_coverage_report"
fi
