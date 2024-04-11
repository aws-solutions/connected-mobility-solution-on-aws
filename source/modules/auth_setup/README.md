# Auth Setup - Compatible with Connected Mobility Solution on AWS modules
<!-- markdownlint-disable-next-line -->
**[Connected Mobility Solution on AWS](https://aws.amazon.com/solutions/implementations/connected-mobility-solution-on-aws/)** | **[🚧 Feature request](https://github.com/aws-solutions/connected-mobility-solution-on-aws/issues/new?assignees=&labels=enhancement&template=feature_request.md&title=)** | **[🐛 Bug Report](https://github.com/aws-solutions/connected-mobility-solution-on-aws/issues/new?assignees=&labels=bug&template=bug_report.md&title=)** | **[❓ General Question](https://github.com/aws-solutions/connected-mobility-solution-on-aws/issues/new?assignees=&labels=question&template=general_question.md&title=)**

**Note**: If you want to use the solution without building from source, navigate to the [AWS Solution Page](https://aws.amazon.com/solutions/implementations/connected-mobility-solution-on-aws/).

## Table of Contents

- [Auth Setup - Compatible with Connected Mobility Solution on AWS modules](#auth-setup---compatible-with-connected-mobility-solution-on-aws-modules)
  - [Table of Contents](#table-of-contents)
  - [Solution Overview](#solution-overview)
  - [Architecture Diagram](#architecture-diagram)
  - [AWS CDK and Solutions Constructs](#aws-cdk-and-solutions-constructs)
  - [Customizing the Module](#customizing-the-module)
  - [Prerequisites](#prerequisites)
    - [MacOS Installation Instructions](#macos-installation-instructions)
    - [Clone the Repository](#clone-the-repository)
    - [Install Required Dependencies](#install-required-dependencies)
    - [Unit Test](#unit-test)
    - [Build the Module](#build-the-module)
    - [Upload Assets to S3](#upload-assets-to-s3)
    - [Deploy on AWS](#deploy-on-aws)
    - [Delete](#delete)
  - [Usage](#usage)
    - [1. Cognito Deploy](#1-cognito-deploy)
    - [2. Empty Config Deploy](#2-empty-config-deploy)
    - [3. Existing Config Deploy](#3-existing-config-deploy)
  - [Cost Scaling](#cost-scaling)
  - [Collection of Operational Metrics](#collection-of-operational-metrics)
  - [License](#license)

## Solution Overview

The Auth Setup module performs two important roles within CMS. First, it provides the means to configure the CMS Auth module's
lambda functions, and other CMS module's client credential flows, via three configuration secrets.

- IdP Config
  - Used by the CMS Auth token validation lambda for validating access tokens with the configured identity provider
- Client Config
  - Used by CMS module's to communicate with the identity provider's `/token` endpoint and execute the client_credentials
flow. Retrieving an access token.
- Authorization Code Exchange Config
  - Used by the CMS Auth authorization code exchange lambda for exchanging an authorization code for an access token.

This module also provides an optional deployment of Cognito infrastructure which is
configured for basic usage within CMS. If deploying the Cognito infrastructure, the configuration secrets will be populated
with the appropriate values. Otherwise, it is necessary for the user to either manually provide the configuration values
for your identity provider of choice after the initial deployment, or specify existing secret arns to use as the configuration
secrets. For more details, see the [Usage](#usage) section.

For more information and a detailed deployment guide, visit the
[CMS Auth Setup](https://docs.aws.amazon.com/solutions/latest/connected-mobility-solution-on-aws/auth-setup.html)
Implementation Guide page.

## Architecture Diagram

[Architecture Diagram](./documentation/architecture/diagrams/auth-setup-architecture-diagram.svg)

## AWS CDK and Solutions Constructs

[AWS Cloud Development Kit (AWS CDK)](https://aws.amazon.com/cdk/) and
[AWS Solutions Constructs](https://aws.amazon.com/solutions/constructs/) make it easier to consistently create
well-architected infrastructure applications. All AWS Solutions Constructs are reviewed by AWS and use best
practices established by the AWS Well-Architected Framework.

In addition to the AWS Solutions Constructs, the solution uses AWS CDK directly to create infrastructure resources.

## Customizing the Module

## Prerequisites

- [Python 3.8+](https://www.python.org/downloads/)
- [NVM](https://github.com/nvm-sh/nvm)
- [NPM 8+](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm)
- [Node 18+](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm)
- [Pipenv](https://pipenv.pypa.io/en/latest/installation.html)

### MacOS Installation Instructions

Pyenv [Github Repository](https://github.com/pyenv/pyenv)

```bash
brew install pyenv
pyenv install 3.10.9
```

Pipenv [Github Repository](https://github.com/pypa/pipenv)

```bash
pip install --user pipenv
pipenv install --dev
```

NVM [Github Repository](https://github.com/nvm-sh/nvm)

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.3/install.sh | bash
```

NPM/Node [Official Documentation](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm)

```bash
nvm install 18
nvm use 18
```

### Clone the Repository

```bash
git clone https://github.com/aws-solutions/connected-mobility-solution-on-aws.git
cd connected-mobility-solution-on-aws/source/modules/auth_setup/
```

### Install Required Dependencies

```bash
make install
```

### Unit Test

After making changes, run unit tests to make sure added customization
pass the tests:

```bash
make test
```

### Build the Module

The build script manages dependencies, builds required assets (e.g. packaged lambdas), and creates the
AWS Cloudformation templates.

```bash
make build
```

### Upload Assets to S3

```bash
make upload
```

### Deploy on AWS

```bash
make deploy
```

### Delete

```bash
make destroy
```

## Usage

The Auth Setup module has three primary deployment paths depending on your existing identity provider setup. These paths
are detailed below.

### 1. Cognito Deploy

If using the optional Cognito infrastructure deployment which is provided by this module, deploy the module with
the CloudFormation parameter `ShouldCreateCognitoResources` set to "True". This will deploy a basic Cognito infrastructure
including a user pool, service app client, and user app client, to your account. It will also populate the three configuration
secrets with values specific to the Cognito deployment.

### 2. Empty Config Deploy

If using your own identity provider, and you do not have existing configuration secrets from a previous deployment,
the Auth Setup module will deploy the three configuration secrets in the expected JSON format with empty values. These
values can be populated after the deployment with values specific to your identity provider. To execute this deployment,
deploy the module with the CloudFormation parameter `ShouldCreateCognitoResources` set to "False", and do not provide
values for the existing secret arn parameters.

### 3. Existing Config Deploy

If using your own identity provider, and you have existing configuration secrets from a previous deployment with
appropriate values that you would like to reuse, the Auth Setup module will connect the existing secrets to SSM parameters
expected by other CMS module's. This can be done for any or all of the three configuration secrets. To execute this deployment,
deploy the module with the CloudFormation parameter `ShouldCreateCognitoResources` set to "False", and provide an existing
secret arn for any of the three existing secret arn CloudFormation parameters.

## Cost Scaling

Cost will scale depending on usage of optional Cognito deployments. Without the Cognito deployment, cost is minimal.

- [Amazon Cognito Cost](https://aws.amazon.com/cognito/pricing/)
- [Amazon Secrets Manager Cost](https://aws.amazon.com/secrets-manager/pricing/)

For more details, see the
[implementation guide](https://docs.aws.amazon.com/solutions/latest/connected-mobility-solution-on-aws/cost.html).

## Collection of Operational Metrics

This solution collects anonymized operational metrics to help AWS improve
the quality and features of the solution. For more information, including
how to disable this capability, please see the
[implementation guide](https://docs.aws.amazon.com/solutions/latest/connected-mobility-solution-on-aws/anonymized-data-collection.html).

## License

Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License").
You may not use this file except in compliance with the License.
You may obtain a copy of the License at <http://www.apache.org/licenses/LICENSE-2.0>

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
