# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

.DEFAULT_GOAL := help

# ========================================================
# LIB METADATA
# ========================================================
export MODULE_NAME ?= $(shell python3 ./setup.py --name)
export MODULE_VERSION ?=  $(shell python3 ./setup.py --version)
export MODULE_DESCRIPTION ?= $(shell python3 ./setup.py --description)
export MODULE_AUTHOR ?= $(shell python3 ./setup.py --author)

SOLUTION_PATH := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/../..)
MODULE_PATH := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))

include ${SOLUTION_PATH}/makefiles/common_config.mk
include ${SOLUTION_PATH}/makefiles/global_targets.mk
include ${SOLUTION_PATH}/makefiles/module_targets.mk

## ========================================================
## INSTALL
## ========================================================
.PHONY: upgrade
upgrade: pipenv-lock ## Upgrades Pipfile.lock.
	@printf "%bPipfile.lock upgrade finished.%b\n" "${GREEN}" "${NC}"
	@printf "%bRun \"make install\" to install upgraded python dependencies.%b\n" "${CYAN}" "${NC}"

.PHONY: install
install: pipenv-sync ## Installs the resources and dependencies required to build the solution.
	@printf "%bInstall finished.%b\n" "${GREEN}" "${NC}"

.PHONY: deploy
deploy: ## Deploy library to pypi - NOT IMPLEMENTED
	@printf "%bLibrary does not yet support deployment to pypi. version=%s%b\n" "${GREEN}" "${MODULE_VERSION}" "${NC}"

.PHONY: destroy
destroy: ## NOT IMPLEMENTED
	@printf "%bLibrary does not support destruction.%b" "${MAGENTA}" "${NC}"

.PHONY: pipenv-setup-sync
pipenv-setup-sync: ## Using pipenv-setup, sync Pipfile.lock and setup.py
ifeq (, $(shell which pipenv-setup))
	$(error pipenv-setup is required to sync setup.py. Run `make install` prior to this target.)
endif
	pipenv-setup sync --pipfile
	@printf "%bRunning `black` to format setup.py.%b\n" "${MAGENTA}" "${NC}"
	-pre-commit run black --files ./setup.py
