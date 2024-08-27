
SHELL := /bin/bash

# Custom location for library installation. OS level file restrictions causes issues.
export MODULE_LIB_DIST_PATH = ${MODULE_PATH}/dist-lib

# JSII_RUNTIME_PACKAGE_CACHE_ROOT is defined so lock collisions don't occur when modules are running concurrently
# - RuntimeError: EEXIST: file already exists, open '<default>/.cache/<path>/aws-cdk-lib/2.130.0/<hash>.lock'
# - https://github.com/aws/jsii/blob/main/packages/%40jsii/kernel/src/tar-cache/default-cache-root.ts
export JSII_RUNTIME_PACKAGE_CACHE_ROOT = ${MODULE_PATH}/.cdk_cache

## ========================================================
## COMMON TARGETS
## ========================================================
.PHONY: pipenv-install
pipenv-install: ## Using pipenv, installs pip dependencies.
	@printf "%bInstalling pip dependencies: %s%b\n" "${MAGENTA}" "${MODULE_NAME}" "${NC}"
	@pipenv install --dev --python ${PYTHON_VERSION}
	@pipenv clean --python ${PYTHON_VERSION}

.PHONY: cdk-solution-helper-install
cdk-solution-helper-install: ## Using npm, installs node modules for cdk-solution-helper.
	@printf "%bInstalling cdk-solution-helper node dependencies: %s%b\n" "${MAGENTA}" "${MODULE_NAME}" "${NC}"
	@npm i --prefix deployment/cdk-solution-helper

.PHONY: build
build: verify-required-tools ## Build templates and assets for the module.
	@printf "%bBuilding the module.%b\n" "${MAGENTA}" "${NC}"
	pipenv run ${MODULE_PATH}/deployment/build-s3-dist.sh

.PHONY: upload
upload: create-upload-bucket ## Upload templates and build assets for the module to S3 buckets.
	@printf "%bUploading S3 assets for the module.%b\n" "${MAGENTA}" "${NC}"
	pipenv run ${MODULE_PATH}/deployment/upload-s3-dist.sh

.PHONY: destroy-stack
destroy-stack: ## Delete the stack for the module.
	@printf "%bDelete the module deployment.%b\n" "${MAGENTA}" "${NC}"
	@aws cloudformation delete-stack --stack-name "${STACK_NAME}"
	@aws cloudformation wait stack-delete-complete --stack-name "${STACK_NAME}"

.PHONY: all
all: build upload deploy ## Rebuild modules, upload assets to s3, and deploy

## ========================================================
## TESTING
## ========================================================
.PHONY: verify-module
verify-module: pre-commit cfn-nag unit-tests ## Run all pre-commits and testing for the module.
	@printf "%bFinished pre-commit and testing.%b\n" "${GREEN}" "${NC}"

.PHONY: test
test: cfn-nag unit-tests ## Run all testing for the module.
	@printf "%bFinished testing.%b\n" "${GREEN}" "${NC}"

.PHONY: pre-commit
pre-commit: ## Run pre-commit for the module.
	@printf "%bRunning pre-commit.%b\n" "${MAGENTA}" "${NC}"
	-pipenv run pre-commit run ${MODULE_NAME} --all-files -c ${SOLUTION_PATH}/.pre-commit-config.yaml

.PHONY: cfn-nag
cfn-nag: ## Run cfn-nag for the module.
	@printf "%bRunning cfn-nag checks.%b\n" "${MAGENTA}" "${NC}"
	pipenv run ${MODULE_PATH}/deployment/run-cfn-nag.sh

.PHONY: unit-tests
unit-tests: ## Run unit-tests for the module.
	@printf "%bRunning unit tests.%b\n" "${MAGENTA}" "${NC}"
	pipenv run ${MODULE_PATH}/deployment/run-unit-tests.sh

.PHONY: update-snapshots
update-snapshots: ## Update snapshot files for the module.
	@printf "%bUpdating unit test snapshots.%b\n" "${MAGENTA}" "${NC}"
	pipenv run ${MODULE_PATH}/deployment/run-unit-tests.sh -r -s

.PHONY: verify-required-tools
verify-required-tools: ## Checks the environment for the required dependencies.
ifneq (v${NODE_VERSION}, $(shell node --version | cut -d "." -f 1-2))
	$(error Node version "v${NODE_VERSION}" is required, as specified in .nvmrc. "$(shell node --version | cut -d "." -f 1-2)" was found instead. Please install the correct version by running `nvm install`.)
endif
ifeq (, $(shell which npm))
	$(error Npm is required and should be automatically installed with node. Please check your node installation.`)
endif
ifeq (, $(shell which yarn))
	$(error Yarn is required, as specified in the README. Please see the following link for installation (OS specific): https://classic.yarnpkg.com/lang/en/docs/install/#mac-stable)
endif
ifneq (Python ${PYTHON_VERSION}, $(shell python --version | cut -d "." -f 1-2))
	$(error Python version "Python ${PYTHON_VERSION}" is required, as specified in .python-version. "$(shell python --version | cut -d "." -f 1-2)" was found instead. Please install the correct version by running `pyenv install -s`)
endif
ifeq (, $(shell which pipenv))
	$(error pipenv is required, as specified in the README. Please see the following link for installation: https://pipenv.pypa.io/en/latest/installation.html)
endif
ifeq (, $(shell which aws))
	$(error The aws CLI is required, as specified in the README. Please see the following link for installation: https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html)
endif
ifeq (, $(shell which cdk))
	$(error The aws-cdk CLI is required, as specified in the README. Please see the following link for installation: https://docs.aws.amazon.com/cdk/v2/guide/cli.html)
endif
	@printf "%bDependencies verified.%b\n" "${GREEN}" "${NC}"

## ========================================================
## HELP COMMANDS
## ========================================================
.PHONY: help
help: ## Displays this help message.
	@grep -E '^[a-zA-Z0-9 -]+:.*##|^##.*'  ${MODULE_PATH}/Makefile | while read -r l; \
	do ( [[ "$$l" =~ ^"##" ]] && printf "%b%s%b\n" "${MAGENTA}" "$$(echo $$l | cut -f 2- -d' ')" "${NC}") \
	|| ( printf "%b%-35s%s%b\n" "${GREEN}" "$$(echo $$l | cut -f 1 -d':')" "$$(echo $$l | cut -f 3- -d'#')" "${NC}"); \
	done;
	@grep -E '^[a-zA-Z0-9 -]+:.*##|^##.*'  ${SOLUTION_PATH}/makefiles/module_targets.mk | while read -r l; \
	do ( [[ "$$l" =~ ^"##" ]] && printf "%b%s%b\n" "${MAGENTA}" "$$(echo $$l | cut -f 2- -d' ')" "${NC}") \
	|| ( printf "%b%-35s%s%b\n" "${GREEN}" "$$(echo $$l | cut -f 1 -d':')" "$$(echo $$l | cut -f 3- -d'#')" "${NC}"); \
	done;

.PHONY: print-module-name
print-module-name: ## Used to get module name safely from any directory if used with make -C
	@printf "${MODULE_NAME}"

.PHONY: version
version: ## Display module name and current version
	@printf "%b%35.35s%b version:%b%s%b\n" $$( [[ "${MODULE_PATH}" = *"lib"* ]] && echo "${YELLOW}" || echo "${CYAN}" ) "${MODULE_NAME}" "${NC}" "${GREEN}" "${MODULE_VERSION}" "${NC}"

.PHONY: get-acdp-deployment-uuid
get-acdp-deployment-uuid: ## Retrieves the deployment-uuid value from the SSM parameter in your AWS account.
ifeq (, $(shell which aws))
	$(error The aws CLI is required, as specified in the README. Please see the following link for installation: https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html)
endif
	@printf "%bRetrieving ACDP Deplyoment UUID.%b\n" "${MAGENTA}" "${NC}"
	aws ssm get-parameter --name=/solution/${ACDP_UNIQUE_ID}/config/deployment-uuid --query Parameter.Value --output text

.PHONY: get-cms-deployment-uuid
get-cms-deployment-uuid: ## Retrieves the deployment-uuid value from the SSM parameter in your AWS account.
ifeq (, $(shell which aws))
	$(error The aws CLI is required, as specified in the README. Please see the following link for installation: https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html)
endif
	@printf "%bRetrieving CMS Deplyoment UUID.%b\n" "${MAGENTA}" "${NC}"
	aws ssm get-parameter --name=/solution/${APP_UNIQUE_ID}/config/deployment-uuid --query Parameter.Value --output text
