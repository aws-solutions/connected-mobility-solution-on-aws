# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

.DEFAULT_GOAL := help

# ========================================================
# SOLUTION METADATA
# ========================================================
export MODULE_NAME ?= vpc
export MODULE_VERSION ?= ${SOLUTION_VERSION}
export MODULE_DESCRIPTION ?= A CDK Python app for deploying opinionated VPC infrastructure usable by CMS modules
export MODULE_AUTHOR ?= AWS Industrial Solutions Team

SOLUTION_PATH := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/../../..)
MODULE_PATH := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))

# ========================================================
# VARIABLES
# ========================================================
export STACK_NAME ?= ${MODULE_NAME}
export STACK_TEMPLATE_NAME = ${MODULE_NAME}.template
export STACK_TEMPLATE_PATH ?= deployment/global-s3-assets/${MODULE_NAME}/${STACK_TEMPLATE_NAME}

export CAPABILITY_ID ?= CMS.23

include ${SOLUTION_PATH}/makefiles/common_config.mk
include ${SOLUTION_PATH}/makefiles/global_targets.mk
include ${SOLUTION_PATH}/makefiles/module_targets.mk

.PHONY: install
install: pipenv-install ## Installs the resources and dependencies required to build the solution.
	@printf "%bInstall finished.%b\n" "${GREEN}" "${NC}"

.PHONY: deploy
deploy: verify-environment ## Deploy the stack for the module.
	@printf "%bDeploy the module.%b\n" "${MAGENTA}" "${NC}"
	aws cloudformation deploy \
		--stack-name ${STACK_NAME} \
		--template-file ${STACK_TEMPLATE_PATH} \
		--s3-bucket ${GLOBAL_ASSET_BUCKET_NAME} \
		--s3-prefix ${SOLUTION_NAME}/local/${MODULE_NAME} \
		--capabilities CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND \
		--parameter-overrides \
 			"VpcName"="${VPC_NAME}" \

.PHONY: destroy
destroy: destroy-stack ## Teardown deployed stack
	@printf "%bDestroy finished.%b\n" "${GREEN}" "${NC}"

## ========================================================
## UTILITY
## ========================================================
.PHONY: verify-environment
verify-environment: ## Checks the cdk environment for the required environment variables, as set via .cmsrc or manual export.
ifneq (, $(wildcard ./cdk.context.json))
	$(error 'cdk.context.json' cannot exist. Please delete the file and try again)
endif
ifndef VPC_NAME
	$(error VPC_NAME is undefined. Set the variable using `export VPC_NAME=...`, run `source .cmsrc` if it exists, or run `make create-rc-file` to generate .cmsrc)
endif
