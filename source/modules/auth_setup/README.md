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
    - [Deployment Options](#deployment-options)
      - [1. Cognito Deploy](#1-cognito-deploy)
      - [2. Empty Config Deploy](#2-empty-config-deploy)
      - [3. Existing Config Deploy](#3-existing-config-deploy)
    - [Integration with ACDP / Backstage](#integration-with-acdp--backstage)
      - [Callback URIs](#callback-uris)
      - [Scopes](#scopes)
    - [Secret Structure](#secret-structure)
      - [IdP Config](#idp-config)
      - [User Client Config](#user-client-config)
      - [Service Client Config](#service-client-config)
    - [SSM Parameter](#ssm-parameter)
  - [Cost Scaling](#cost-scaling)
  - [Collection of Operational Metrics](#collection-of-operational-metrics)
  - [License](#license)

## Solution Overview

The Auth Setup module supports the following features within CMS:

- Create IdP configuration for CMS Auth module's Token Validation and Authorization Code Exchange lambda functions
- Create IdP configuration for Users to login to the Backstage module
- Create IdP configuration for CMS modules to perform service-to-service auth via the Client Credentials flow
- Provide an optional deployment of Cognito infrastructure compatible with Backstage, and populate the IdP configurations
  appropriately

These features are accomplished primarily via three AWS Secrets Manager secrets, which provide configuration structure
for any OAuth 2.0 identity provider. The secrets are as follows:

- IdP Config
  - IdP configurations needed to facilitate authentication and authorization via OAuth 2.0 identity providers.
- Service Client Config
  - Service client configuration needed for OAuth 2.0 operations.
- User Client Config
  - User client configuration needed for OAuth 2.0 operations.

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

- [Python 3.12+](https://www.python.org/downloads/)
- [NVM](https://github.com/nvm-sh/nvm)
- [NPM 8+](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm)
- [Node 18+](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm)
- [Pipenv](https://pipenv.pypa.io/en/latest/installation.html)

### MacOS Installation Instructions

Pyenv [Github Repository](https://github.com/pyenv/pyenv)

```bash
brew install pyenv
pyenv install 3.12
```

Pipenv [Github Repository](https://github.com/pypa/pipenv)

```bash
pip install --user pipenv
pipenv sync --dev
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

### Deployment Options

The Auth Setup module has three primary deployment paths depending on your existing identity provider setup. These paths
are detailed below.

#### 1. Cognito Deploy

If using the optional Cognito infrastructure deployment which is provided by this module, deploy the module with
the CloudFormation parameter `ShouldCreateCognitoResources` set to "True". This will deploy a basic Cognito infrastructure
including a user pool, service app client, and user app client, to your account. It will also populate the three configuration
secrets and one SSM Parameter with values specific to the Cognito deployment.

#### 2. Empty Config Deploy

If using your own identity provider, and you do not have existing configuration secrets from a previous deployment,
the Auth Setup module will deploy the three configuration secrets in the expected JSON format as well as one
SSM Parameter with empty values. These
values can be populated after the deployment with values specific to your identity provider. To execute this deployment,
deploy the module with the CloudFormation parameter `ShouldCreateCognitoResources` set to "False", and do not provide
values for the existing secret arn parameters.

#### 3. Existing Config Deploy

If using your own identity provider, and you have existing configuration secrets from a previous deployment with
appropriate values that you would like to reuse, the Auth Setup module will connect the existing secrets to SSM parameters
expected by other CMS module's. This can be done for any or all of the three configuration secrets. To execute this deployment,
deploy the module with the CloudFormation parameter `ShouldCreateCognitoResources` set to "False", and provide an existing
secret arn for any of the three existing secret arn CloudFormation parameters.

### Integration with ACDP / Backstage

#### Callback URIs

If you would like to use the Auth Setup module for authenticating logins to the Backstage portal deployed by ACDP, it is
necessary to include the appropriate Backstage Callback URI in your identity provider's user client. This Callback Uri
is defined as '<https://your-backstage-domain/api/auth/provider-id/handler/frame>'. See the backstage docs for more info:
<https://backstage.io/docs/auth/oidc#the-configuration>.

This value is added by default to the Cognito user app client when deploying Cognito infrastructure, and when deploying via
the Makefile `make deploy` target, by using the `FULLY_QUALIFIED_DOMAIN_NAME` environment variable (this is the same variable
used to set the Backstage domain during an ACDP / Backstage deploy). Otherwise, you must configure the Callback URIs for
your identity provider client manually to facilitate the Backstage login redirect.

#### Scopes

To allow login to Backstage, the IdP must be configured to allow the following three scopes: openid, email,
profile. Without these scopes, Backstage will fail to authenticate users on login. This can be adjusted from the Backstage
source code if desired.

### Secret Structure

#### IdP Config

- issuer
  - Issuer URL for the IdP that will be included in the `iss` claim of access tokens
- token_endpoint
  - `/oauth2/token` endpoint for the IdP
- authorization_endpoint
  - `/oauth2/authorize` endpoint for the IdP
- alternate_aud_key
  - Claim key to use for validating access tokens instead of `aud`, if `aud` is not including in the access tokens provided
    by your IdP
- auds
  - Array of allowed audience values for the `aud` claim of access tokens
- scopes
  - Array of scopes used to validate the `scopes` claim of access tokens

#### User Client Config

- client_id
  - Client ID of User client
- client_secret
  - Client Secret of User client

#### Service Client Config

- client_id
  - Client ID of Service client
- client_secret
  - Client Secret of Service client

### SSM Parameter

- Cognito user pool Id

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
