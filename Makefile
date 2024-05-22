# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

.DEFAULT_GOAL := help
SHELL := /bin/bash

include makefiles/common_config.mk
include makefiles/global_targets.mk

## ========================================================
## INCLUDE MODULE'S MAKEFILE TARGETS
## ========================================================
module_name-target: ## Call a module make target. Run "make module_name-help" for target lists. Run "ls source/modules" for module list.

MODULES := source/lib $(shell find ${SOLUTION_PATH}/source/modules -type d -maxdepth 1 -mindepth 1 -not -name __pycache__)
GLOBAL_TARGETS := $(shell grep -E '^[a-zA-Z0-9-]+:' ${SOLUTION_PATH}/makefiles/global_targets.mk | awk -F: '/^[^.]/ {print $$1;}')
COMMON_TARGETS := $(shell grep -E '^[a-zA-Z0-9-]+:' ${SOLUTION_PATH}/makefiles/module_targets.mk | awk -F: '/^[^.]/ {print $$1;}')

## $2が hoge/fuga/piyoだと
## hoge fuga piyo にsubstで分割されて
## piyo が lastwordで選択されて
## piyo-$1
## Makefile のターゲットを動的に生成している。
define make-module-target
$(lastword $(subst /, ,$2))-$1:
	@$(MAKE) -C $2 -f Makefile $1
endef


## 動作例
## 前提条件：
##    hogeディレクトリ内のMakefileには、buildとinstallの2つのターゲットが定義されています。
##    fugaディレクトリ内のMakefileには、cleanとtestの2つのターゲットが定義されています。
##
## 具体的な動作：
##    foreachループが最初のディレクトリであるhogeに対して実行されます。
##    hogeディレクトリのMakefileからターゲット名を抽出し、buildとinstallという2つのターゲットが取得されます。
##    make-module-targetマクロが2回呼び出されて、hoge-buildとhoge-installの2つのターゲットルールが動的に生成されます。
##    次に、foreachループが2番目のディレクトリであるfugaに対して同じプロセスを実行します。
##    fugaディレクトリのMakefileからターゲット名を抽出し、cleanとtestという2つのターゲットが取得されます。
##    make-module-targetマクロが2回呼び出されて、fuga-cleanとfuga-testの2つのターゲットルールが動的に生成されます。
## hoge-build:
##     @$(MAKE) -C hoge -f Makefile build
## hoge-install:
##     @$(MAKE) -C hoge -f Makefile install
## 
## fuga-clean:
##     @$(MAKE) -C fuga -f Makefile clean
## 
## fuga-test:
##     @$(MAKE) -C fuga -f Makefile test
$(foreach module,$(MODULES),$(foreach element,$(shell grep -E '^[a-zA-Z0-9-]+:' $(module)/Makefile | awk -F: '/^[^.]/ {print $$1;}'),$(eval $(call make-module-target,$(element),$(module)))))

## modulename-command:
##     @$(MAKE) -C modulename-f Makefile command
## みたいなのがglobal及びcommonに定義されたコマンドから生成される
$(foreach module,$(MODULES),$(foreach target,$(GLOBAL_TARGETS),$(eval $(call make-module-target,$(target),$(module)))))
$(foreach module,$(MODULES),$(foreach target,$(COMMON_TARGETS),$(eval $(call make-module-target,$(target),$(module)))))

## ========================================================
## INVOKE MAKE TARGET FROM EACH MODULES' MAKEFILE
## ========================================================
SubMakefiles    = source/lib/ $(shell find source \( -name lib -o -name deployment -o -name cdk.out -o -name .venv -o -name node_modules -o -name backstage \) -prune -false -o -name Makefile)
SubMakeDirs     = $(filter-out ${SOLUTION_PATH},$(dir $(SubMakefiles)))
Prereqs         = source/modules/vpc/ source/modules/auth_setup/ source/modules/cms_config/ source/modules/cms_auth/ source/modules/cms_connect_store/ source/modules/cms_alerts/ source/modules/cms_api/
DeployableDirs  = $(filter-out source/lib/ source/modules/cms_sample_on_aws ${Prereqs},${SubMakeDirs})

define run-module-target
	run_make_with_logging() { \
		output=$$(make -C "$$1" $1 2>&1); \
		module_target_exit_code=$$?; \
		if [[ $$module_target_exit_code -ne 0 ]]; then \
			printf "%bFinished %sMakefile %s failed.\n%s\n%b\n" "${RED}" "$$1" "$1" "$$output" "${NC}"; \
		else \
			printf "%bFinished %sMakefile %s passed.%b\n" "${GREEN}" "$$1" "$1" "${NC}"; \
		fi; \
		return $$module_target_exit_code; \
	}; \
	did_make_target_fail=0; \
	process_pids=(); \
	for dir in $2; do \
		printf "%bStarting %sMakefile %s.%b\n" "${MAGENTA}" "$$dir" "$1" "${NC}"; \
		(run_make_with_logging "$$dir") & process_pids+=($$!); \
	done; \
	for pid in $${process_pids[@]}; do wait "$${pid}" || did_make_target_fail=1; done; \
	exit $$did_make_target_fail;
endef

.PHONY: install
install: root-install ## Call root and all modules' "make install".
	@$(call run-module-target,install,${SubMakeDirs})
	@printf "%bFinished install.%b\n" "${GREEN}" "${NC}"

.PHONY: build
build: ## Call all modules' "make build".
	@printf "%bStarting build.%b\n" "${MAGENTA}" "${NC}"
	@$(call run-module-target,build,${SubMakeDirs})
	@printf "%bFinished build.%b\n" "${GREEN}" "${NC}"

.PHONY: deploy
deploy: deploy-variables ## Call all modules' "make deploy". Order enforced.
	@printf "%bStarting deploy.%b\n" "${MAGENTA}" "${NC}"
	@for dir in $(Prereqs); do \
		printf "%bDeploying %s.%b\n" "${MAGENTA}" "$$dir" "${NC}"; \
		$(MAKE) -C $$dir deploy || exit $$?; \
	done
	@$(call run-module-target,deploy,${DeployableDirs})
	@printf "%bFinished deploy.%b\n" "${GREEN}" "${NC}"
	@printf "%bView status:%b %bhttps://%s.console.aws.amazon.com/cloudformation/home?region=%s%b\n" "${YELLOW}" "${NC}" "${CYAN}" "${AWS_REGION}" "${AWS_REGION}" "${NC}"

.PHONY: destroy
destroy: ## Call all modules' "make destroy". Order enforced.
	@printf "%bStarting destroy.%b\n" "${MAGENTA}" "${NC}"
	@$(call run-module-target,destroy,${DeployableDirs})
	@reversed=$$(printf "%s\n" ${Prereqs} | tail -r | xargs echo); \
	for dir in $${reversed}; do \
		printf "%bDestroying %s.%b\n" "${MAGENTA}" "$$dir" "${NC}"; \
		$(MAKE) -C $$dir destroy || exit $$?; \
	done
	@printf "%bFinished destroy.%b\n" "${GREEN}" "${NC}"
	@printf "%bView status:%b %bhttps://%s.console.aws.amazon.com/cloudformation/home?region=%s%b\n" "${YELLOW}" "${NC}" "${CYAN}" "${AWS_REGION}" "${AWS_REGION}" "${NC}"

.PHONY: upload
upload: create-upload-bucket upload-backstage-assets-zip ## Call root and all modules' "make upload" and upload backstage assets zip.
	@$(call run-module-target,upload,${SubMakeDirs})
	@printf "%bFinished upload.%b\n" "${MAGENTA}" "${NC}"
	@printf "%bView resources:%b %bhttps://s3.console.aws.amazon.com/s3/buckets/%s-%s?region=%s%b\n" "${YELLOW}" "${NC}" "${CYAN}" "${S3_ASSET_BUCKET_BASE_NAME}" "${AWS_REGION}" "${AWS_REGION}" "${NC}"

.PHONY: upload-backstage-assets-zip
upload-backstage-assets-zip:
	@aws s3api put-object \
        --bucket "${REGIONAL_ASSET_BUCKET_NAME}" \
        --key "${SOLUTION_NAME}/${SOLUTION_VERSION}/backstage.zip" \
        --body "${SOLUTION_PATH}/deployment/regional-s3-assets/backstage.zip" \
        --expected-bucket-owner "${AWS_ACCOUNT_ID}" > /dev/null
	@printf "%bFinished uploading zipped backstage assets \n%b" "${GREEN}" "${NC}"

.PHONY: verify-module
verify-module: ## Run all verifications for CMS. CAUTION: Takes a long time.
	@$(call run-module-target,verify-module,${SubMakeDirs})
	@printf "%bFinished verify-module.%b\n" "${GREEN}" "${NC}"

.PHONY: cfn-nag
cfn-nag: ## Run cfn-nag for the entire solution.
	@$(call run-module-target,cfn-nag,${SubMakeDirs})
	@printf "%bFinished cfn-nag.%b\n" "${GREEN}" "${NC}"

.PHONY: unit-tests
unit-tests:  ## Run unit-tests for the entire solution.
	@$(call run-module-target,unit-tests,${SubMakeDirs})
	@printf "%bFinished unit tests.%b\n" "${GREEN}" "${NC}"

.PHONY: test
test:  ## Run cfn-nag and unit-tests for the entire solution.
	@$(call run-module-target,test,${SubMakeDirs})
	@printf "%bFinished test.%b\n" "${GREEN}" "${NC}"

.PHONY: update-snapshots
update-snapshots:  ## Run update-snapshots for the entire solution.
	@$(call run-module-target,update-snapshots,${SubMakeDirs})
	@printf "%bFinished update-snapshots.%b\n" "${GREEN}" "${NC}"

.PHONY: version
version: root-version ## Display solution name and current version and each module's version
	@process_pids=(); \
	for dir in $(SubMakeDirs); do $(MAKE) -C $$dir version & process_pids+=($$!); done; \
	for pid in $${process_pids[@]}; do wait "$${pid}"; done;

## ========================================================
## INSTALL
## ========================================================
.PHONY: root-install
root-install: ## Using pipenv, installs pip dependencies for root.
	@printf "%bInstalling pip dependencies.%b\n" "${MAGENTA}" "${NC}"
	pipenv install --dev --python ${PYTHON_VERSION}
	pipenv clean --python ${PYTHON_VERSION}

## ========================================================
## BUILD
## ========================================================
.PHONY: asset-copy
asset-copy: ## Copy modules' build artifacts to root level folders
	@printf "%bCopying global assets to ${SOLUTION_PATH}/deployment%b\n" "${MAGENTA}" "${NC}"
	@rm -rf ${SOLUTION_PATH}/deployment/global-s3-assets && mkdir ${SOLUTION_PATH}/deployment/global-s3-assets
	@find source \( -name cdk.out -o -name .venv -o -name node_modules -o -name backstage -o -name build \) -prune -false -o -name "global-s3-assets" -exec bash -c "cp -r {}/* ${SOLUTION_PATH}/deployment/global-s3-assets" \;
	@printf "%bCopying regional assets to ${SOLUTION_PATH}/deployment%b\n" "${MAGENTA}" "${NC}"
	@rm -rf ${SOLUTION_PATH}/deployment/regional-s3-assets && mkdir ${SOLUTION_PATH}/deployment/regional-s3-assets
	@find source \( -name cdk.out -o -name .venv -o -name node_modules -o -name backstage -o -name build \) -prune -false -o -name "regional-s3-assets" -exec bash -c "cp -r {}/* ${SOLUTION_PATH}/deployment/regional-s3-assets" \;
	@printf "%bFinished asset collation.%b\n" "${GREEN}" "${NC}"

.PHONY: zip-backstage-assets
zip-backstage-assets: ## Zip backstage assets in the regional assets directory
	@cd ${SOLUTION_PATH}/deployment/regional-s3-assets/backstage && zip -r ${SOLUTION_PATH}/deployment/regional-s3-assets/backstage.zip . > /dev/null
	@printf "%bFinished zipping backstage assets \n%b" "${GREEN}" "${NC}"

.PHONY: build-open-source
build-open-source: ## Build open source distribution
	${SOLUTION_PATH}/deployment/build-open-source-dist.sh --solution-name ${SOLUTION_NAME}

.PHONY: build-all
build-all: build asset-copy zip-backstage-assets ## Builds all modules and copies assets to top level deployment folder.

## ========================================================
## TESTING
## ========================================================
.PHONY: pre-commit-all
pre-commit-all: ## Run pre-commit for the entire solution for all files.
	@printf "%bRunning all pre-commits.%b\n" "${MAGENTA}" "${NC}"
	-pipenv run pre-commit run --all-files

## ========================================================
## UTILITY
## ========================================================
.PHONY: clean-build-artifacts
clean-build-artifacts: ## Cleans up build files, not including venvs, dependencies, or release build artifacts.
	@printf "%bRunning clean script.%b\n" "${MAGENTA}" "${NC}"
	${SOLUTION_PATH}/deployment/run-clean-build-artifacts.sh
	@printf "%bFinished clean script.%b\n" "${GREEN}" "${NC}"

.PHONY: clean-build-artifacts-release
clean-build-artifacts-release: ## Cleans up build files, including release build artifacts.
	@printf "%bRunning clean script.%b\n" "${MAGENTA}" "${NC}"
	${SOLUTION_PATH}/deployment/run-clean-build-artifacts.sh --release-build
	@printf "%bFinished clean script.%b\n" "${GREEN}" "${NC}"

.PHONY: clean-build-artifacts-dependencies
clean-build-artifacts-dependencies: ## Cleans up build files, including venvs and dependencies.
	@LOCK_FILES_OPTION="--lock-files"; \
	if [ "$${PIPELINE_TYPE}" = "dtas" ]; then \
		LOCK_FILES_OPTION=""; \
	fi; \
	printf "%bRunning clean scripts.%b\n" "${MAGENTA}" "${NC}"; \
	${SOLUTION_PATH}/deployment/run-clean-build-artifacts.sh --dependencies $$LOCK_FILES_OPTION
	@printf "%bFinished clean script.%b\n" "${GREEN}" "${NC}"

.PHONY: clean-build-artifacts-all
clean-build-artifacts-all: ## Cleans up existing build files, including venvs, dependencies, and release build artifacts.
	@printf "%bRunning clean script.%b\n" "${MAGENTA}" "${NC}"
	${SOLUTION_PATH}/deployment/run-clean-build-artifacts.sh --all
	@printf "%bFinished clean script.%b\n" "${GREEN}" "${NC}"

.PHONY: deploy-variables
deploy-variables: ## Get variable values to deploy with.
	@[[ -f .cmsrc ]] || printf "%bInstead of using this target, you can run the following command.\n%b" "${MAGENTA}" "${NC}"
	@[[ -f .cmsrc ]] || printf "%bcat > .cmsrc <<EOL\nexport USER_EMAIL=\"jie_liu@example.com\"\nexport VPC_NAME=\"cms-vpc\"\nexport IDENTITY_PROVIDER_ID=\"cms\"\nexport ROUTE53_ZONE_NAME=\"domain.com\"\nexport ROUTE53_BASE_DOMAIN=\"subdomain.domain.com\"\nexport BACKSTAGE_NAME=\"Default Name\"\nexport BACKSTAGE_ORG=\"Default Name\"\nEOL\n%b" "${YELLOW}" "${NC}"
	@source .cmsrc \
	[[ -n $${USER_EMAIL} ]] || read -p "Enter User Email: " USER_EMAIL; \
	[[ -n $${ROUTE53_ZONE_NAME} ]] || read -p "Enter Route53 Zone Name: " ROUTE53_ZONE_NAME; \
	[[ -n $${ROUTE53_BASE_DOMAIN} ]] || read -p "Enter Route53 Base Domain: " ROUTE53_BASE_DOMAIN; \
	[[ -n $${VPC_NAME} ]] || read -p "Enter VPC Name: " VPC_NAME; \
	[[ -n $${IDENTITY_PROVIDER_ID} ]] || read -p "Enter Identity Provider ID: " IDENTITY_PROVIDER_ID; \
	[[ -n $${BACKSTAGE_NAME} ]] || read -p "Enter Backstage Name: " BACKSTAGE_NAME; \
	[[ -n $${BACKSTAGE_ORG} ]] || read -p "Enter Backstage Organization: " BACKSTAGE_ORG; \
	printf "#!/bin/bash\nexport USER_EMAIL=\"%s\"\nexport ROUTE53_ZONE_NAME=\"%s\"\nexport ROUTE53_BASE_DOMAIN=\"%s\"\nexport VPC_NAME=\"%s\"\nexport IDENTITY_PROVIDER_ID=\"%s\"\nexport BACKSTAGE_NAME=\"%s\"\nexport BACKSTAGE_ORG=\"%s\"\n" "$$USER_EMAIL" "$$ROUTE53_ZONE_NAME" "$$ROUTE53_BASE_DOMAIN" "$$VPC_NAME" "$$IDENTITY_PROVIDER_ID" "$$BACKSTAGE_NAME" "$$BACKSTAGE_ORG" > .cmsrc

.PHONY: generate-python-requirements-files
generate-python-requirements-files: ## Generates requirements.txt files from the pipfiles throughout the solution.
	@printf "%bGenerating requirements.txt from pipfiles.%b\n" "${MAGENTA}" "${NC}"\
	find ${SOLUTION_PATH} \( -name .venv -o -name node_modules -o -name "cdk.out" \) -prune -false -o -name "Pipfile" -execdir bash -c "echo; PIPENV_PIPFILE={} pipenv requirements 1> requirements.txt;" \;

## ========================================================
## HELPERS
## ========================================================
.PHONY: help
help: ## Displays this help message. For a module's help, run "make <module_name>-help".
	@grep -E '^[a-zA-Z0-9 -_]+:.*##|^##.*'  ${SOLUTION_PATH}/Makefile | while read -r l; \
	do ( [[ "$$l" =~ ^"##" ]] && printf "%b%s%b\n" "${MAGENTA}" "$$(echo $$l | cut -f 2- -d' ')" "${NC}") \
	|| ( printf "%b%-35s%s%b\n" "${GREEN}" "$$(echo $$l | cut -f 1 -d':')" "$$(echo $$l | cut -f 3- -d'#')" "${NC}"); \
	done;

.PHONY: encourage
encourage: ## Sometimes we all need a little encouragement!
	@printf "%bYou can do this. Believe in yourself. :)%b\n" "${GREEN}" "${NC}"

.PHONY: root-version
root-version: ## Display solution name and current version
	@printf "%b%35.35s%b version:%b%s%b\n" "${MAGENTA}" "${SOLUTION_NAME}" "${NC}" "${GREEN}" "${SOLUTION_VERSION}" "${NC}"
