#!/bin/bash

# Find and execute all similarly named scripts, but not if in cdk.out or itself (infinite loops are fun)
base_directory=$PWD

# If a module failure occurs, we will exit with a failed status code at the end, but we still want to run every module's script
did_module_script_failure_occur=0

while IFS= read -r -d '' file; do
    # The module specific script file name is in $file
    echo ""
    echo "===================================================="
    echo "Running $file"
    echo "===================================================="
    echo ""

    $file ${@:2}
    most_recent_module_script_exit_code=$?

    # Check the result of the script and mark if a failure is identified
    if [[ $most_recent_module_script_exit_code -ne 0 ]]
    then
        echo ""
        echo "===================================================="
        echo "Module Script Failure: $file FAILED in $base_directory"
        echo "===================================================="
        echo ""
        did_module_script_failure_occur=1
    fi

    # module script might have called cd, bring us back
    cd $base_directory
done < <(find . -name "$1" -not -path "**/cdk.out/*" -not -path "./deployment/*" -not -path "**/node_modules/*" -print0)

# We return whether a module script occured so we can exit appropriately in the higher level script
exit $did_module_script_failure_occur
