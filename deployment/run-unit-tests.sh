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

-n, --no-nested          Don't run module level versions of this script

-r, --no-report          Don't generate the report, this is mainly used for pre-commit

EOF
# EOF is found above and hence cat command stops reading. This is equivalent to echo but much neater when printing out.
}

# $@ is all command line parameters passed to the script.
# -o is for short options like -v
# -l is for long options with double dash like --version
# the comma separates different long options
# -a is for long options with single dash like -version
options=$(getopt -l "help,no-nested,no-report" -o "hnr" -a -- "$@")
generate_report=true
run_nested_commands=true

while true
do
  case "$1" in
    -h|--help)
        showHelp
        exit 0
        ;;
    -n|--no-nested)
        run_nested_commands=false
        ;;
    -r|--no-report)
        generate_report=false
        ;;
    *)
        shift
        break;;
  esac
  shift
done

# Activate local environment
echo "===================================================="
echo "Activating venv found in $PWD"
echo "===================================================="
source ./.venv/bin/activate

[ "$DEBUG" == 'true' ] && set -x

# Get reference for all important folders
project_dir=$PWD
source_dir="$project_dir/source"
tests_dir="$source_dir/tests"
metrics_tests_dir="$source_dir/infrastructure/handlers/metrics/app/tests"
backstage_tests_dir="$source_dir/backstage/cdk/source/tests"
coverage_reports_top_path="$source_dir/tests/coverage-reports"
backstage_dir="$source_dir/backstage"
backstage_frontend_dir="$source_dir/backstage/packages/app"
backstage_backend_dir="$source_dir/backstage/packages/backend"

rm -rf $project_dir/.coverage

# Run test on package and save results to coverage_report_path in xml format
python_coverage_report="$coverage_reports_top_path/coverage.xml"
if [ $generate_report = true ]
then
  pytest $tests_dir $backstage_tests_dir $metrics_tests_dir \
    --cov=$source_dir  \
    --cov-report=term \
    --cov-report=xml:$python_coverage_report \
    --cov-config=$project_dir/.coveragerc \
    --snapshot-update
else
  pytest $tests_dir $backstage_tests_dir $metrics_tests_dir \
    --cov=$source_dir  \
    --cov-report=term \
    --cov-config=$project_dir/.coveragerc
fi
did_cmdp_failure_occur=$?

# Check the result of the test and echo if a failure was detected. Don't exit yet so the rest of the module tests will run.
if [[ $did_cmdp_failure_occur -ne 0 ]]
then
  echo "===================================================="
  echo "test FAILED for $source_dir"
  echo "===================================================="
fi

# Linux and MacOS have different ways of calling the sed command for in-place editing.
# MacOS takes a mandatory argument for the -i flag whereas linux does not.
sedi=(-i)
if [[ "$OSTYPE" == "darwin"* ]]; then
  sedi=(-i "")
fi
# The pytest coverage report xml generated has the absolute path of the files
# when reporting coverage. Replace the absolute path with the relative path from
# the project's root directory so that SonarQube can understand the coverage report.
sed "${sedi[@]}" -e "s,<source>$source_dir,<source>source,g" $python_coverage_report

# <=====UNIQUE TO BACKSTAGE=====>
yarn --cwd=$backstage_dir install

# Run tests for backstage front-end console application
npm run test --prefix=$backstage_frontend_dir
did_backstage_frontend_failure_occur=$?

# Check results of front-end tests
if [[ $did_backstage_frontend_failure_occur -ne 0 ]]
then
  echo "===================================================="
  echo "test FAILED for $backstage_frontend_dir"
  echo "===================================================="
fi

# Run tests for backstage backend
npm run test --prefix=$backstage_backend_dir
did_backstage_backend_failure_occur=$?

# Check results of backend tests
if [[ $did_backstage_backend_failure_occur -ne 0 ]]
then
  echo "===================================================="
  echo "test FAILED for $backstage_backend_dir"
  echo "===================================================="
fi

rm -rf $backstage_frontend_dir/coverage/lcov-report
rm -rf $backstage_backend_dir/coverage/lcov-report
# <=====UNIQUE TO BACKSTAGE=====>

# <=====UNIQUE TO TOP LEVEL SCRIPT=====>
# Run the same script for all of the individual modules
did_module_script_failure_occur=0
if [ $run_nested_commands = true ]
then
  $project_dir/deployment/run-module-scripts.sh $(basename $0) $@
  did_module_script_failure_occur=$?
fi
# <=====UNIQUE TO TOP LEVEL SCRIPT=====>

# Check the results of the module specific tests and exit if a failure is identified
# Don't echo because the echo was done in the run-module-scripts.sh script
if [[ $did_module_script_failure_occur -ne 0 || $did_cmdp_failure_occur -ne 0 || $did_backstage_frontend_failure_occur -ne 0 || $did_backstage_backend_failure_occur -ne 0 ]]
then
  exit 1
fi
