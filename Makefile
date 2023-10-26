# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

-include .env

.DEFAULT_GOAL := help

# ========================================================
# VARIABLES
# ========================================================
PYTHON_VERSION ?= 3.10.9
AWS_ACCOUNT_ID=$(shell aws sts get-caller-identity --query "Account" --output text)
PIPENV_VENV_IN_PROJECT = 1
STAGE ?= dev
AWS_REGION ?= $(shell aws configure get region --output text)
CDK_DEPLOY_REGION = ${AWS_REGION}
ROUTE53_BASE_DOMAIN ?= ${ROUTE53_ZONE_NAME}
BACKSTAGE_WEB_PORT ?= 443
BACKSTAGE_WEB_SCHEME ?= https
VPC_CIDR_RANGE ?= 10.0.0.0/16
BACKSTAGE_LOG_LEVEL ?= info
CMS_SOLUTION_VERSION ?= v0.0.0
CMS_RESOURCE_BUCKET ?= ${AWS_ACCOUNT_ID}-cms-resources-${AWS_REGION}
CMS_RESOURCE_BUCKET_REGION ?= ${AWS_REGION}
BACKSTAGE_TEMPLATE_S3_KEY_PREFIX ?= ${CMS_SOLUTION_VERSION}/backstage/templates
BACKSTAGE_TEMPLATE_S3_UPDATE_REFRESH_MINS ?= 30
BACKSTAGE_NAME ?= DEFAULT_NAME
BACKSTAGE_ORG ?= DEFAULT_ORG

# Call export after all variables are set.
# This alllows Make variables to be used and environment variables in sub-shells created by Make target commands
export

# ==================================================================================
# PRINT COLORS
# 	To use, simply add ${<color>}<text> to get the colored text.
#   To disable color, add ${NC} at the point you'd like it to stop.
#   printf is recommended over echo if wanting color because of more multi-platform support.
# ==================================================================================
LIGHT_GREEN = \033[1;32m
GREEN = \033[0;32m
LIGHT_PURPLE = \033[1;35m
NC = \033[00m

.PHONY: install
install: pipenv-install pipenv-clean node-package-install ## Installs the resources and dependencies required to build the solution.
	@printf "${LIGHT_PURPLE}Install finished.${NC}\n"

.PHONY: node-package-install
node-package-install: ## Using npm, installs yarn, the aws-cdk-lib, and node dependencies for all modules.
	@printf "${LIGHT_PURPLE}Checking for yarn installation and installing if not found.${NC}\n"
	npm install -g yarn
	@printf "${LIGHT_PURPLE}Checking for cdk installation and installing if not found.${NC}\n"
	npm install -g aws-cdk
	@printf "${LIGHT_PURPLE}Installing node dependencies using yarn.${NC}\n"
	find . -name "package.json" -not -path "*node_modules*" -not -path "*cdk-solution-helper*" -not -path "*cdk.out*" -path "*backstage*" -not -path "*examples*" -execdir bash -c "echo 'Installing from yarn '; pwd; yarn install " {} \;
	@printf "${LIGHT_PURPLE}Installing node dependencies using npm.${NC}\n"
	find . -name "package.json" -not -path "*node_modules*" -not -path "*cdk-solution-helper*" -not -path "*cdk.out*" -not -path "*backstage*" -execdir bash -c "echo 'Installing from npm '; pwd; npm install;" {} \;

.PHONY: pipenv-install
pipenv-install: ## Using pipenv, installs pip dependencies for all modules.
	@printf "${LIGHT_PURPLE}Installing pip dependencies.${NC}\n"
	find . -name "Pipfile" -not -path "*cdk.out*" -exec bash -c "echo; echo 'Installing from ' {}; PIPENV_IGNORE_VIRTUALENVS=1 PIPENV_PIPFILE={} PIPENV_VENV_IN_PROJECT=1 pipenv install --dev --python ${PYTHON_VERSION}" {} \;

.PHONY: gen-python-requirements
gen-python-requirements: ## Generates requirements.txt files from the pipfiles throughout the solution.
	@printf "${LIGHT_PURPLE}Generating requirements.txt from pipfiles.${NC}\n"
	find . -name "Pipfile" -not -path "*cdk.out*" -execdir bash -c "echo; PIPENV_IGNORE_VIRTUALENVS=1 PIPENV_PIPFILE={} PIPENV_VENV_IN_PROJECT=1 pipenv requirements 1> requirements.txt; echo" {} \;

## ========================================================
## PIPENV VIRTUAL ENVIRONMENT MANAGEMENT
## ========================================================
.PHONY: pipenv-lock
pipenv-lock: ## Generates Pipfile.lock for all modules (pipenv lock).
	@printf "${LIGHT_PURPLE}Generating Pipfile.lock from Pipfiles.${NC}\n"
	find . -name "Pipfile" -not -path "*cdk.out*" -exec bash -c "echo; echo 'Installing from ' {}; PIPENV_IGNORE_VIRTUALENVS=1 PIPENV_PIPFILE={} PIPENV_VENV_IN_PROJECT=1 pipenv lock --dev --python ${PYTHON_VERSION}" {} \;

.PHONY: pipenv-sync
pipenv-sync: ## Installs all packages specified in Pipfile.lock for all modules (pipenv sync).
	@printf "${LIGHT_PURPLE}Syncing virtual environments with Pipfile.lock.${NC}\n"
	find . -name "Pipfile" -not -path "*cdk.out*" -exec bash -c "echo; echo 'Installing from ' {}; PIPENV_IGNORE_VIRTUALENVS=1 PIPENV_PIPFILE={} PIPENV_VENV_IN_PROJECT=1 pipenv sync --dev --python ${PYTHON_VERSION}" {} \;

.PHONY: pipenv-update
pipenv-update: ## Runs lock then sync. (pipenv update).
	@printf "${LIGHT_PURPLE}Beginning pipenv update (lock and sync).${NC}\n"
	find . -name "Pipfile" -not -path "*cdk.out*" -exec bash -c "echo; echo 'Updating from ' {}; PIPENV_IGNORE_VIRTUALENVS=1 PIPENV_PIPFILE={} PIPENV_VENV_IN_PROJECT=1 pipenv update --dev --python ${PYTHON_VERSION}" {} \;

.PHONY: pipenv-clean
pipenv-clean: ## Uninstalls all packages not specified in Pipfile.lock (pipenv clean).
	@printf "${LIGHT_PURPLE}Cleaning virtual environment of packages not in Pipfile.lock.${NC}\n"
	find . -name "Pipfile" -not -path "*cdk.out*" -exec bash -c "echo; echo 'Cleaning from ' {}; PIPENV_IGNORE_VIRTUALENVS=1 PIPENV_PIPFILE={} PIPENV_VENV_IN_PROJECT=1 pipenv clean --dry-run --python ${PYTHON_VERSION}" {} \;

## ========================================================
## SYNTH AND DEPLOY
## ========================================================

.PHONY: synth
synth: ## Runs cdk synth for Backstage and CMS core.
	@printf "${LIGHT_PURPLE}Synthesizing Backstage and CMS core.${NC}\n"
	cdk synth \
	--context "user-email"="${USER_EMAIL}" \
	--context "route53-zone-name"="${ROUTE53_ZONE_NAME}" \
	--context "route53-base-domain"="${ROUTE53_BASE_DOMAIN}" \
	--context "web-port"="${BACKSTAGE_WEB_PORT}" \
	--context "web-scheme"="${BACKSTAGE_WEB_SCHEME}" \
	--context "vpc-cidr-range"="${VPC_CIDR_RANGE}" \
	--context "backstage-name"="${BACKSTAGE_NAME}" \
	--context "backstage-org"="${BACKSTAGE_ORG}" \
	--context "backstage-log-level"="${BACKSTAGE_LOG_LEVEL}" \
	--context "cms-resource-bucket"="${CMS_RESOURCE_BUCKET}" \
	--context "cms-resource-bucket-region"="${CMS_RESOURCE_BUCKET_REGION}" \
	--context "cms-resource-bucket-backstage-template-key-prefix"="${BACKSTAGE_TEMPLATE_S3_KEY_PREFIX}" \
	--context "cms-resource-bucket-backstage-refresh-frequency-mins"="${BACKSTAGE_TEMPLATE_S3_UPDATE_REFRESH_MINS}" \
	--context "nag-enforce"=True \
	--quiet


.PHONY: synth-staging
synth-staging: ## Runs cdk synth for Backstage and CMS core, and ouputs to ./deployment/staging.
	@printf "${LIGHT_PURPLE}Synthesizing Backstage and CMS core for staging (./deployment/staging).${NC}\n"
	cdk synth \
	--context "user-email"="${USER_EMAIL}" \
	--context "route53-zone-name"="${ROUTE53_ZONE_NAME}" \
	--context "route53-base-domain"="${ROUTE53_BASE_DOMAIN}" \
	--context "web-port"="${BACKSTAGE_WEB_PORT}" \
	--context "web-scheme"="${BACKSTAGE_WEB_SCHEME}" \
	--context "vpc-cidr-range"="${VPC_CIDR_RANGE}" \
	--context "backstage-name"="${BACKSTAGE_NAME}" \
	--context "backstage-org"="${BACKSTAGE_ORG}" \
	--context "backstage-log-level"="${BACKSTAGE_LOG_LEVEL}" \
	--context "cms-resource-bucket"="${CMS_RESOURCE_BUCKET}" \
	--context "cms-resource-bucket-region"="${CMS_RESOURCE_BUCKET_REGION}" \
	--context "cms-resource-bucket-backstage-template-key-prefix"="${BACKSTAGE_TEMPLATE_S3_KEY_PREFIX}" \
	--context "cms-resource-bucket-backstage-refresh-frequency-mins"="${BACKSTAGE_TEMPLATE_S3_UPDATE_REFRESH_MINS}" \
	--context "nag-enforce"=True \
	--output="./deployment/staging" \
	--quiet

.PHONY: cdk-context
cdk-context: check-cdk-env ## Displays current cdk context.
	@printf "${LIGHT_PURPLE}Verifying CDK Context.${NC}\n"
	cdk context \
	--context "user-email"="${USER_EMAIL}" \
	--context "route53-zone-name"="${ROUTE53_ZONE_NAME}" \
	--context "route53-base-domain"="${ROUTE53_BASE_DOMAIN}" \
	--context "web-port"="${BACKSTAGE_WEB_PORT}" \
	--context "web-scheme"="${BACKSTAGE_WEB_SCHEME}" \
	--context "vpc-cidr-range"="${VPC_CIDR_RANGE}" \
	--context "backstage-name"="${BACKSTAGE_NAME}" \
	--context "backstage-org"="${BACKSTAGE_ORG}" \
	--context "backstage-log-level"="${BACKSTAGE_LOG_LEVEL}" \
	--context "cms-resource-bucket"="${CMS_RESOURCE_BUCKET}" \
	--context "cms-resource-bucket-region"="${CMS_RESOURCE_BUCKET_REGION}" \
	--context "cms-resource-bucket-backstage-template-key-prefix"="${BACKSTAGE_TEMPLATE_S3_KEY_PREFIX}" \
	--context "cms-resource-bucket-backstage-refresh-frequency-mins"="${BACKSTAGE_TEMPLATE_S3_UPDATE_REFRESH_MINS}"


.PHONY: deploy
deploy: check-cdk-env clean ## Runs make clean, then builds and deploys Backstage and CMS core.
	@printf "${LIGHT_PURPLE}Deploying Backstage and CMS core.${NC}\n"
	cdk deploy \
	--context "user-email"="${USER_EMAIL}" \
	--context "route53-zone-name"="${ROUTE53_ZONE_NAME}" \
	--context "route53-base-domain"="${ROUTE53_BASE_DOMAIN}" \
	--context "web-port"="${BACKSTAGE_WEB_PORT}" \
	--context "web-scheme"="${BACKSTAGE_WEB_SCHEME}" \
	--context "vpc-cidr-range"="${VPC_CIDR_RANGE}" \
	--context "backstage-name"="${BACKSTAGE_NAME}" \
	--context "backstage-org"="${BACKSTAGE_ORG}" \
	--context "backstage-log-level"="${BACKSTAGE_LOG_LEVEL}" \
	--context "cms-resource-bucket"="${CMS_RESOURCE_BUCKET}" \
	--context "cms-resource-bucket-region"="${CMS_RESOURCE_BUCKET_REGION}" \
	--context "cms-resource-bucket-backstage-template-key-prefix"="${BACKSTAGE_TEMPLATE_S3_KEY_PREFIX}" \
	--context "cms-resource-bucket-backstage-refresh-frequency-mins"="${BACKSTAGE_TEMPLATE_S3_UPDATE_REFRESH_MINS}"

.PHONY: bootstrap
bootstrap: check-cdk-env ## Bootstraps Backstage and CMS core.
	@printf "${LIGHT_PURPLE}Bootstrapping Backstage and CMS core.${NC}\n"
	cdk bootstrap \
	--context "user-email"="${USER_EMAIL}" \
	--context "route53-zone-name"=${ROUTE53_ZONE_NAME} \
	--context "route53-base-domain"=${ROUTE53_BASE_DOMAIN} \
	--context "web-port"=${BACKSTAGE_WEB_PORT} \
	--context "web-scheme"=${BACKSTAGE_WEB_SCHEME} \
	--context "vpc-cidr-range"=${VPC_CIDR_RANGE} \
	--context "backstage-name"="${BACKSTAGE_NAME}" \
	--context "backstage-org"="${BACKSTAGE_ORG}" \
	--context "backstage-log-level"="${BACKSTAGE_LOG_LEVEL}" \
	--context "cms-resource-bucket"="${CMS_RESOURCE_BUCKET}" \
	--context "cms-resource-bucket-region"="${CMS_RESOURCE_BUCKET_REGION}" \
	--context "cms-resource-bucket-backstage-template-key-prefix"="${BACKSTAGE_TEMPLATE_S3_KEY_PREFIX}" \
	--context "cms-resource-bucket-backstage-refresh-frequency-mins"="${BACKSTAGE_TEMPLATE_S3_UPDATE_REFRESH_MINS}"

.PHONY: upload-s3-deployment-assets
upload-s3-deployment-assets: clean  ## Runs make clean, then uploads required deployment assets to S3 for deploying CMS modules via Backstage and Proton.
	@printf "${LIGHT_PURPLE}Beginning S3 setup.${NC}\n"
	@printf "${LIGHT_PURPLE}Creating and uploading proton service templates (./deployment/create-proton-service-templates.sh).${NC}\n"
	./deployment/create-proton-service-templates.sh
	@printf "${LIGHT_PURPLE}Copying module source code and template.yaml files to S3. (./deployment/copy-backstage-templates-to-s3.sh).${NC}\n"
	./deployment/copy-backstage-templates-to-s3.sh
	@printf "${LIGHT_PURPLE}Finished setting up S3.${NC}\n"

.PHONY: get-deployment-uuid
get-deployment-uuid: ## Retrieves the deployment-uuid value from the ssm parameter in your AWS account
	@printf "${LIGHT_PURPLE}Retrieving Deplyoment UUID.${NC}\n"
	aws ssm get-parameter --name=/${STAGE}/cms/common/config/deployment-uuid --query Parameter.Value --output text

## ========================================================
## UTILITY COMMANDS
## ========================================================
.PHONY: clean
clean: ## Cleans up existing build files, not including venvs or dependencies.
	@printf "${LIGHT_PURPLE}Running clean scripts.${NC}\n"
	./deployment/clean-for-deploy.sh

.PHONY: check-cdk-env
check-cdk-env: ## Checks the cdk environment for the required environment variables and dependencies.
ifneq (v18.17.1, $(shell node --version))
	$(error Node version 18.17.1 is required, as specified in .nvmrc. Please install by running `nvm install`)
endif
ifneq (9.6.7, $(shell npm --version))
	$(error Npm version 3.10.9 is required, as specified by the node version in .nvmrc. Please check your node installation.`)
endif
ifneq (Python 3.10.9, $(shell python --version))
	$(error Python version 3.10.9 is required, as specified in .python-version. Please install by running `pyenv install -s`)
endif
ifneq (, $(wildcard ./cdk.context.json))
	$(error 'cdk.context.json' cannot exist, please delete and try again)
endif
ifndef USER_EMAIL
	$(error USER_EMAIL is undefined. Set the variable using `export USER_EMAIL=...`, or use a .env file)
endif
ifndef ROUTE53_ZONE_NAME
	$(error ROUTE53_ZONE_NAME is undefined. Set the variable using `export USER_EMAIL=...`, or use a .env file)
endif
ifndef ROUTE53_BASE_DOMAIN
	$(error ROUTE53_BASE_DOMAIN is undefined. Set the variable using `export USER_EMAIL=...`, or use a .env file)
endif
	@printf "${GREEN}All required environment variables found.${NC}\n"

## ========================================================
## HELP COMMANDS
## ========================================================
.PHONY: help
help: ## Displays usage information about the Makefile in a readable format.
	@grep -E '^[a-zA-Z0-9 -]+:.*##|^##.*'  Makefile | while read -r l; \
	do ( [[ "$$l" =~ ^"##" ]] && printf "${LIGHT_PURPLE}%s${NC}\n" "$$(echo $$l | cut -f 2- -d' ')") \
	|| ( printf "${LIGHT_GREEN}%-30s${NC}%s\n" "$$(echo $$l | cut -f 1 -d':')" "$$(echo $$l | cut -f 3- -d'#')"); \
	done;

.PHONY: list-rules
list-rules: ## Displays an alphabetical list of the makefile rules with their descriptions.
	@grep -E '^[a-zA-Z0-9 -]+:.*##'  Makefile | sort | while read -r l; do printf "${LIGHT_GREEN}%-30s${NC}%s\n" "$$(echo $$l | cut -f 1 -d':')" "$$(echo $$l | cut -f 3- -d'#')"; done
