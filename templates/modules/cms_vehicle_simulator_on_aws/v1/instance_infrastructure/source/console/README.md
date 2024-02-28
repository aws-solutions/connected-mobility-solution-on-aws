# Connected Mobility Solution on AWS - Vehicle Simulator Console

**[Connected Mobility Solution on AWS](https://aws.amazon.com/solutions/implementations/connected-mobility-solution-on-aws/)** | **[🚧 Feature request](https://github.com/aws-solutions/connected-mobility-solution-on-aws/issues/new?assignees=&labels=enhancement&template=feature_request.md&title=)** | **[🐛 Bug Report](https://github.com/aws-solutions/connected-mobility-solution-on-aws/issues/new?assignees=&labels=bug&template=bug_report.md&title=)** | **[❓ General Question](https://github.com/aws-solutions/connected-mobility-solution-on-aws/issues/new?assignees=&labels=question&template=general_question.md&title=)**

**Note**: If you want to use the solution without building from source, navigate to the [AWS Solution Page](https://aws.amazon.com/solutions/implementations/connected-mobility-solution-on-aws/).

## Table of Contents
- [Connected Mobility Solution on AWS - Vehicle Simulator Console](#connected-mobility-solution-on-aws---vehicle-simulator-console)
  - [Table of Contents](#table-of-contents)
  - [Solution Overview](#solution-overview)
  - [Architecture Diagram](#architecture-diagram)
  - [AWS CDK and Solutions Constructs](#aws-cdk-and-solutions-constructs)
  - [Customizing the Module](#customizing-the-module)
  - [Prerequisites](#prerequisites)
      - [MacOS Installation Instructions](#macos-installation-instructions)
    - [Clone the Repository](#clone-the-repository)
    - [Unit Test](#unit-test)
    - [Build](#build)
      - [Build Using Script](#build-using-script)
      - [Manually Build](#manually-build)
    - [Deploy](#deploy)
      - [One-click deploy](#one-click-deploy)
      - [Deploy using script](#deploy-using-script)
      - [Manually deploy](#manually-deploy)
  - [Cost Scaling](#cost-scaling)
  - [Collection of Operational Metrics](#collection-of-operational-metrics)
  - [License](#license)

## Solution Overview

The CMS Vehicle Simulator is an engine designed to enable customers to get started quickly assessing AWS IoT services
without an existing pool of devices. This solution leverages managed, highly available, highly scalable AWS-native
services to create and simulate thousands of connected devices that are pre-defined or created by the customer.

For more information and a detailed deployment guide, visit the
[CMS Vehicle Simulator](https://docs.aws.amazon.com/solutions/latest/connected-mobility-solution-on-aws/vehicle-simulator-module.html) solution page.

## Architecture Diagram

![Architecture Diagram](../../documentation/architecture/diagrams/cms-vehicle-simulator-architecture-diagram.svg)

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

#### MacOS Installation Instructions

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
git clone https://github.com/aws-solutions/connected-mobility-solution-on-aws
cd connected-mobility-solution-on-aws/templates/modules/cms_vehicle_simulator_on_aws
```

### Unit Test

After making changes, run unit tests to make sure added customization passes the tests:

```bash
chmod +x deployment/run-unit-tests.sh
./deployment/run-unit-tests.sh
```

### Build

#### Build Using Script

The build script manages dependencies, builds required assets (e.g. packaged lambdas), and creates the
AWS Cloudformation templates.

```bash
./deployment/build-s3-dist.sh $DIST_OUTPUT_BUCKET $TEMPLATE_OUTPUT_BUCKET $SOLUTION_NAME $VERSION
```

Upload AWS Cloudformation templates

```bash

```

#### Manually Build

Install development packages

```bash
pipenv install --dev
```

Synthesize into Cloudformation

```bash
cdk synth
```

### Deploy

#### One-click deploy

- Get the link of the `cms-vehicle-simulator-on-aws.template` uploaded to your Amazon S3 bucket.
- Deploy the CMS Vehicle Simulator solution to your account by launching a new AWS CloudFormation stack using
the S3 link of the `cms-vehicle-simulator-on-aws.template`.

#### Deploy using script

```bash
./deployment/deploy-s3-dist.sh
```

#### Manually deploy

```bash
cdk deploy --parameters useremail=admin@email.com
```

## Cost Scaling

Basic usage (small simulations for short durations) should stay within the free tier.

## Collection of Operational Metrics

This solution collects anonymized operational metrics to help AWS improve
the quality and features of the solution. For more information, including
how to disable this capability, please see the
[implementation guide](https://docs.aws.amazon.com/solutions/latest/connected-mobility-solution-on-aws/operational-metrics.html).

## License

Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License").
You may not use this file except in compliance with the License.
You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
