#!/bin/bash
#
# This assumes all of the OS-level configuration has been completed and git repo has already been cloned
#
# This script should be run from the repo's deployment directory
# ./run-unit-tests.sh
#

showHelp() {
# `cat << EOF` This means that cat should stop reading when EOF is detected
cat << EOF
Usage: ./deployment/run-unit-tests.sh --help
Run unit tests in this project.

-h, --help               Display help

-r, --no-report          Don't generate the report, this is mainly used for pre-commit

EOF
# EOF is found above and hence cat command stops reading. This is equivalent to echo but much neater when printing out.
}

# $@ is all command line parameters passed to the script.
# -o is for short options like -v
# -l is for long options with double dash like --version
# the comma separates different long options
# -a is for long options with single dash like -version
options=$(getopt -l "help,no-report" -o "hr" -a -- "$@")
generate_report=true

while true
do
  case "$1" in
    -h|--help)
        showHelp
        exit 0
        ;;
    -r|--no-report)
        generate_report=false
        break
        ;;
    *)
        shift
        break;;
  esac
  shift
done

[ "$DEBUG" == 'true' ] && set -x

# If getting called from CMS, change PWD to the expected location
cms_root_dir=""
if [[ "$0" == *"templates"* ]]; then
  cms_root_dir="$PWD"
  while IFS='/' read -ra ADDR; do
    for i in "${ADDR[@]}"; do
      if [[ "$i" == "deployment" ]]; then
        break
      fi
      cd $i
    done
  done <<< "$0"
fi

# Activate local environment
echo "===================================================="
echo "Activating venv found in $PWD"
echo "===================================================="
source ./.venv/bin/activate

# Get reference for all important folders
project_dir="$PWD"
source_dir="$project_dir/source"
tests_dir="$source_dir/tests"
coverage_reports_top_path="$source_dir/tests/coverage-reports"
python_coverage_report="$coverage_reports_top_path/coverage.xml"

rm -rf $project_dir/.coverage

# Run test on package and save results to coverage_report_path in xml format
if [ $generate_report = true ]
then
  pytest $tests_dir \
    --cov=$project_dir  \
    --cov-report=term \
    --cov-report=xml:$python_coverage_report \
    --cov-config=$project_dir/.coveragerc \
    --snapshot-update
else
  pytest $tests_dir \
    --cov=$project_dir  \
    --cov-report=term \
    --cov-config=$project_dir/.coveragerc
fi
did_test_failure_occur=$?

# Check the result of the test and exit if a failure is identified
if [[ $did_test_failure_occur -ne 0 ]]
then
    echo "===================================================="
    echo "test FAILED for $source_dir"
    echo "===================================================="
    exit 1
fi

# Only perform the sed transformation if a report was generated, to guarantee the coveragereport file exists
if [ $generate_report = true ]
then
  # Linux and MacOS have different ways of calling the sed command for in-place editing.
  # MacOS takes a mandatory argument for the -i flag whereas linux does not.
  sedi=(-i)
  if [[ "$OSTYPE" == "darwin"* ]]; then
    sedi=(-i "")
  fi

  # The pytest coverage report xml generated has the absolute path of the files
  # when reporting coverage. Replace the absolute path with the relative path from
  # the project's root directory so that SonarQube can understand the coverage report.
  if [[ $cms_root_dir != "" ]]; then
    sed "${sedi[@]}" -e "s,<source>$cms_root_dir/,<source>,g" $python_coverage_report
  fi
fi
