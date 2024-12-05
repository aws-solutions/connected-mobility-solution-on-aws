# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

.DEFAULT_GOAL := help

# ========================================================
# SOLUTION METADATA
# ========================================================
export MODULE_NAME ?= cms-vehicle-simulator
export MODULE_SHORT_NAME ?= vehicle-simulator
export MODULE_VERSION ?= ${SOLUTION_VERSION}
export MODULE_DESCRIPTION ?= A CDK Python app to simulate vehicles using AWS IoT Core
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

export CAPABILITY_ID ?= CMS.1

include ${SOLUTION_PATH}/makefiles/common_config.mk
include ${SOLUTION_PATH}/makefiles/global_targets.mk
include ${SOLUTION_PATH}/makefiles/module_targets.mk

.PHONY: npm-clean-install
npm-clean-install: ## Using npm, installs node dependencies from package-lock.json.
	@printf "%bInstalling node dependencies using npm.%b\n" "${MAGENTA}" "${NC}"
	@npm ci --prefix source/console

# Although npm supports updating package-lock.json without performing an installation, since yarn does not, and yarn is used elsewhere
# in the solution, for consistent behavior across updating node dependencies, an install is also performed here.
# This behavior is different from the pipenv-lock targets, which do not perform an install, and only upgrade Pipfile.lock.
# If upgrading to modern yarn, this target should be updated to only perform a lockfile update without install.
.PHONY: npm-update
npm-update: ## Checks for node dependency upgrades and updates package-lock.json, then performs an install.
	@printf "%bUpgrading package-lock.json and installing node dependencies.%b\n" "${MAGENTA}" "${NC}"
	@npm update --prefix source/console

.PHONY: upgrade
upgrade: pipenv-lock npm-update ## Checks for dependency upgrades and updates lock files. Does not install python dependencies.
	@printf "%bFinished upgrading lock files and installing node dependencies.%b\n" "${GREEN}" "${NC}"
	@printf "%bRun \"make install\" to install updated python dependencies.%b\n" "${CYAN}" "${NC}"

.PHONY: install
install: pipenv-sync npm-clean-install cdk-solution-helper-clean-install ## Installs the resources and dependencies required to build the solution.
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
			"DefaultUserEmail"="${DEFAULT_USER_EMAIL}" \

.PHONY: destroy
destroy: destroy-stack ## Teardown deployed stack
	@printf "%bDestroy finished.%b\n" "${GREEN}" "${NC}"

.PHONY: verify-environment
verify-environment: ## Checks for the required environment variables.
ifneq (, $(wildcard ./cdk.context.json))
	$(error 'cdk.context.json' cannot exist. Please delete the file and try again)
endif
ifndef DEFAULT_USER_EMAIL
	$(error DEFAULT_USER_EMAIL is undefined. Set the variable using `export DEFAULT_USER_EMAIL=...`, run `source .cmsrc` if it exists, or run `make create-rc-file` to generate .cmsrc)
endif
	@printf "%bEnvironment variables verified.%b\n" "${GREEN}" "${NC}"
