#!/bin/bash

set -e && [[ "$DEBUG" == 'true' ]] && set -x

showHelp() {
cat << EOF
Usage: ./deployment/run-cfn-nag.sh --help

Run "cdk-nag" and cfn-nag in this module.

-dl, --deny-list-path       Pass the file name which contains cfn-nag rules to suppress

EOF
}

while [[ $# -gt 0 ]]
do
key="$1"
  case $key in
    -h|--help)
        showHelp
        exit 0
        ;;
    -dl|--deny-list-path)
        deny_list_path="$2"
        shift
        shift
        ;;
    *)
        shift
  esac
done

cd "$(dirname "$0")"/..

# Get reference for all important folders
root_dir="$(dirname "$(dirname "$(realpath "$0")")")"
deployment_dir="$root_dir/deployment"
template_dist_dir="$deployment_dir/global-s3-assets"

# Run the build script to build the assets and templates
printf "%bBuild the assets for the module.%b\n" "${MAGENTA}" "${NC}"
export CDK_NAG_ENFORCE=true
make -C "$root_dir" build

did_cfn_nag_fail=0
# Loop through all files with extension .template in the template_dist_dir
while IFS=  read -r file; do
    # Check if the file exists and is a file (not a directory)
    if [[ -f "${file}" ]]; then
        # Fail if exit code is non-0. The if statement is necessary to prevent exit because of `set -e`.
        if ! output=$(cfn_nag "${file}" ${deny_list_path:+--deny-list-path=$deny_list_path} 2>&1); then
            did_cfn_nag_fail=1
            printf "%bCFN NAG scan failed with failures.%b\n" "${RED}" "${NC}"
        fi
        # Check if there are any warnings in the output. cfn_nag does not return a failing exit code on warnings.
        if [[ "${output}" == *"WARN"* ]]; then
            did_cfn_nag_fail=1
            printf "%bCFN NAG scan failed with warnings.%b\n" "${RED}" "${NC}"
        fi
        echo "$output"
    fi
done < <(find "$template_dist_dir" -name "*.template" -mindepth 1 -type f)

exit $did_cfn_nag_fail
