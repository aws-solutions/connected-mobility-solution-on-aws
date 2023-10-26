#!/bin/bash

showHelp() {
# `cat << EOF` This means that cat should stop reading when EOF is detected
cat << EOF
Usage: ./deployment/run-cfn-nag.sh --help

Run "cdk-nag" and cfn-nag in this project.

-h, --help               Display help

-dl, --deny-list-path  Pass the file name which contains cfn-nag rules to suppress

EOF
# EOF is found above and hence cat command stops reading. This is equivalent to echo but much neater when printing out.
}

# $@ is all command line parameters passed to the script.
# -o is for short options like -v
# -l is for long options with double dash like --version
# the comma separates different long options
# -a is for long options with single dash like -version
options=$(getopt -l "help,deny-list-path,no-nested" -o "hRN" -a -- "$@")
deny_list_path=""
run_nested_commands=true

while true
do
  case "$1" in
    -h|--help)
        showHelp
        exit 0
        ;;
    -dl|--deny-list-path)
        deny_list_path="$2"
        shift
        ;;
    -n|--no-nested)
        run_nested_commands=false
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

cdk_out_dir=$PWD/cdk.out

# Synthesize the latest stack template files
rm -rf $cdk_out_dir
make synth
did_cdk_synth_fail=$?

did_cmdp_nag_failure_occur=0
if [[ $did_cdk_synth_fail -ne 0 ]]
then
    echo "===================================================="
    echo "CDK SYNTH failed, can not perform CFN NAG Scan"
    echo "===================================================="
    did_cmdp_nag_failure_occur=1
else
    # Loop through all files with extension .template.json inside the cdk.out folder
    for file in "${cdk_out_dir}"/*.template.json
    do
        # Check if the file exists and is a file (not a directory)
        if [[ -f "${file}" ]]; then
            # Run cfn_nag on the file
            if [ "$deny_list_path" == "" ]; then
                output=$(cfn_nag "${file}"  2>&1)
            else
                output=$(cfn_nag "${file}" --deny-list-path=$deny_list_path 2>&1)
            fi
            # Check if there are any warnings in the output
            if [[ "${output}" == *"WARN"* ]]; then
                # Set the warnings_exist flag to true
                warnings_exist=true
            fi
            # Check if there are any failures in the output
            if [[ "${output}" == *"FAIL"* ]]; then
                # Set the failures_exist flag to true
                failures_exist=true
            fi
            echo "$output"
        fi
    done
    # If there were any warnings or failures, note them, but don't exit yet so the rest of the module scripts will run.
    if [[ "${warnings_exist}" = true || "${failures_exist}" = true ]]; then
        echo "===================================================="
        echo "CFN NAG Scan failed"
        echo "===================================================="
        did_cmdp_nag_failure_occur=1
    fi
fi

# <=====UNIQUE TO TOP LEVEL SCRIPT=====>
# Run the same script for all of the individual modules
did_module_script_failure_occur=0
if [ $run_nested_commands = true ]
then
  $PWD/deployment/run-module-scripts.sh $(basename $0) $@
  did_module_script_failure_occur=$?
fi
# <=====UNIQUE TO TOP LEVEL SCRIPT=====>

# Check if module or cmdp failures occured, and exit accordingly
if [[ $did_module_script_failure_occur -ne 0 || $did_cmdp_nag_failure_occur -ne 0 ]]
then
    exit 1
fi
