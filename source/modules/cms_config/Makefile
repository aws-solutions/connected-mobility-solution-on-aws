# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

.DEFAULT_GOAL := help

# ========================================================
# SOLUTION METADATA
# ========================================================
export MODULE_NAME ?= cms-config
export MODULE_SHORT_NAME ?= config
export MODULE_VERSION ?= ${SOLUTION_VERSION}
export MODULE_DESCRIPTION ?= A CDK Python app for creating a CMS configuration module
export MODULE_AUTHOR ?= AWS Industrial Solutions Team

SOLUTION_PATH := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/../../..)
MODULE_PATH := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))

# ========================================================
# VARIABLES
# ========================================================
export APP_UNIQUE_ID ?= cms

export STACK_NAME ?= ${APP_UNIQUE_ID}-app--${MODULE_NAME}
export STACK_TEMPLATE_NAME = ${MODULE_NAME}.template
export STACK_TEMPLATE_PATH ?= deployment/global-s3-assets/${MODULE_NAME}/${STACK_TEMPLATE_NAME}

export CAPABILITY_ID ?= CMS.26

include ${SOLUTION_PATH}/makefiles/common_config.mk
include ${SOLUTION_PATH}/makefiles/global_targets.mk
include ${SOLUTION_PATH}/makefiles/module_targets.mk

.PHONY: upgrade
upgrade: pipenv-lock ## Upgrades Pipfile.lock.
	@printf "%bPipfile.lock upgrade finished.%b\n" "${GREEN}" "${NC}"
	@printf "%bRun \"make install\" to install upgraded python dependencies.%b\n" "${CYAN}" "${NC}"

.PHONY: install
install: pipenv-sync cdk-solution-helper-clean-install ## Installs the resources and dependencies required to build the solution.
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
			"AppUniqueId"="${APP_UNIQUE_ID}" \
			"VpcName"="${VPC_NAME}" \
			"IdentityProviderId"="${IDENTITY_PROVIDER_ID}" \

.PHONY: destroy
destroy: destroy-stack ## Teardown deployed stack
	@printf "%bDestroy finished.%b\n" "${GREEN}" "${NC}"

.PHONY: verify-environment
verify-environment: ## Checks for the required environment variables.
ifneq (, $(wildcard ./cdk.context.json))
	$(error 'cdk.context.json' cannot exist. Please delete the file and try again)
endif
ifndef IDENTITY_PROVIDER_ID
	$(error IDENTITY_PROVIDER_ID is undefined. Set the variable using `export IDENTITY_PROVIDER_ID=...`, run `source .cmsrc` if it exists, or run `make create-rc-file` to generate .cmsrc)
endif
ifndef VPC_NAME
	$(error VPC_NAME is undefined. Set the variable using `export VPC_NAME=...`, run `source .cmsrc` if it exists, or run `make create-rc-file` to generate .cmsrc)
endif
	@printf "%bEnvironment variables verified.%b\n" "${GREEN}" "${NC}"
