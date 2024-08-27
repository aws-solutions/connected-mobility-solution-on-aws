# Connected Mobility Solution on AWS - FleetWise Connector Module
<!-- markdownlint-disable-next-line -->
**[Connected Mobility Solution on AWS](https://aws.amazon.com/solutions/implementations/connected-mobility-solution-on-aws/)** | **[🚧 Feature request](https://github.com/aws-solutions/connected-mobility-solution-on-aws/issues/new?assignees=&labels=enhancement&template=feature_request.md&title=)** | **[🐛 Bug Report](https://github.com/aws-solutions/connected-mobility-solution-on-aws/issues/new?assignees=&labels=bug&template=bug_report.md&title=)** | **[❓ General Question](https://github.com/aws-solutions/connected-mobility-solution-on-aws/issues/new?assignees=&labels=question&template=general_question.md&title=)**

**Note**: If you want to use the solution without building from source, navigate to the [AWS Solution Page](https://aws.amazon.com/solutions/implementations/connected-mobility-solution-on-aws/).

## Table of Contents

- [Connected Mobility Solution on AWS - FleetWise Connector Module](#connected-mobility-solution-on-aws---fleetwise-connector-module)
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
    - [AWS IoT FleetWise](#aws-iot-fleetwise)
    - [Query the Data in Timestream and Athena](#query-the-data-in-timestream-and-athena)
  - [Cost Scaling](#cost-scaling)
  - [Collection of Operational Metrics](#collection-of-operational-metrics)
  - [License](#license)

## Solution Overview

CMS FleetWise Connector is a deployable module within [Connected Mobility Solution on AWS](/README.md) (CMS)
that provides the required resources and roles to consume data from AWS IoT FleetWise campaigns into CMS.

For more information and a detailed deployment guide, visit the
[CMS FleetWise Connector](https://docs.aws.amazon.com/solutions/latest/connected-mobility-solution-on-aws/fleetwise-connector-module.html)
Implementation Guide page.

## Architecture Diagram

![Architecture Diagram](./documentation/architecture/diagrams/cms-fleetwise-connector-architecture-diagram.svg)

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
- [Pipenv](https://pipenv.pypa.io/en/latest/installation/)

### MacOS Installation Instructions

Pyenv [Github Repository](https://github.com/pyenv/pyenv)

```bash
brew install pyenv
pyenv install 3.12
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
cd connected-mobility-solution-on-aws/source/modules/cms_fleetwise_connector/
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

### AWS IoT FleetWise

AWS IoT FleetWise must be configured separately from this module. Instructions for configuring AWS IoT FleetWise
in the AWS Console can be found [here](https://docs.aws.amazon.com/iot-fleetwise/latest/developerguide/getting-started-console-tutorial.html)

When creating a [AWS IoT FleetWise Campaign](https://docs.aws.amazon.com/iot-fleetwise/latest/developerguide/create-campaign.html),
the resources created by this module should be used as the storage configuration.

Information about the Amazon Timestream storage configuration parameters is stored in SSM Parameters at the following locations:

| Property                            | SSM Path                                                                 |
|-------------------------------------|--------------------------------------------------------------------------|
| Timestream DB Name                  | /solution/{app_unique_id}/fleetwise-connector/timestream/database/name   |
| Timestream DB ARN                   | /solution/{app_unique_id}/fleetwise-connector/timestream/database/arn    |
| Timestream DB Region                | /solution/{app_unique_id}/fleetwise-connector/timestream/database/region |
| Timestream Table Name               | /solution/{app_unique_id}/fleetwise-connector/timestream/table/name      |
| Timestream Table ARN                | /solution/{app_unique_id}/fleetwise-connector/timestream/database/arn    |
| FleetWise Campaign Storage IAM Role | /solution/{app_unique_id}/fleetwise-connector/fleetwise/execution-role   |

### Query the Data in Timestream and Athena

AWS IoT FleetWise campaigns store data for near real time queries in Timestream.
For historical queries, the Athena tables created via the Glue Crawler should be used.

## Cost Scaling

Cost will scale based on the size of the data stored in Timestream and S3 as
well as compute utilized by AWS Step Functions and AWS Glue Crawlers.

- [AWS IoT FleetWise Cost](https://aws.amazon.com/iot-fleetwise/pricing/)
- [Amazon Timestream Cost](https://aws.amazon.com/timestream/pricing/)
- [AWS Step Functions Cost](https://aws.amazon.com/step-functions/pricing/)
- [AWS Glue Crawlers Cost](https://aws.amazon.com/glue/pricing/)

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
