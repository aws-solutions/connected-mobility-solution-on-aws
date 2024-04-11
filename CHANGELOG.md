# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2024-04-11

### Added

#### Common

- Added all applicable ACDP and CMS on AWS module resources to VPC.
- Created VPC module to provide a reference VPC implementation for ACDP and CMS on AWS Modules.
- Added one-click deployment support via CloudFormation templates.
- Created Make targets for build, upload, and deploy process.

#### ACDP

- Replaced AWS Proton with custom build orchestration via Amazon CodeBuild from Backstage.
- Created ACDP plugins for Backstage to assist with CI/CD operations of CMS on AWS modules and external solutions.

#### CMS

- Created Auth Setup module which adds support for choosing between Cognito or a compatible OAuth 2.0 compliant IdP.
- Created CMS Config module to define common configurations within the solution.
- Added TechDocs support to CMS Modules.

### Fixed

- Updates to Backstage to resolve various issues in plugins.

## [1.0.4] - 2024-02-28

### Fixed

- Upgrade backstage to 1.23.3 to mitigate vulnerability.
- Fix a bug that could occur if the s3 version of the backstage source was prefixed with a special character.


## [1.0.3] - 2024-02-23

### Fixed

- Added resolution for the ECDSA package to mitigate vulnerability.
- Added resolution for the cyrptography package to mitigate vulnerability.
- Added resolution for node-ip package to mitigate vulnerability.


## [1.0.2] - 2024-01-10

### Fixed

- Updated Grafana workspace in EV Battery Health module to include.
plugin management and install Amazon Athena plugin.
- Added resolution for octokit package to mitigate vulnerability.
- Added resolution for follow-redirects package to mitigate vulnerability.
- Added resolution for swagger-ui-react package to address Backstage build failure.
- Removed `yarn tsc:full` from backstage image build.
- Add ignore pattern for Axios in vehicle simulator to ensure correct version usage.

## [1.0.1] - 2023-11-15

### Fixed

- Updated various README URLs to the correct values.
- Resolved an issue where the Aurora PostgresSQL cluster's version defaulted to 11 instead of 13 in some regions.
- Pinned Node and Python versions in Proton manifest.yml for every module.

## [1.0.0] - 2023-09-05

### Added

#### CMS Modules

- CMS Alerts
- CMS API
- CMS Authentication
- CMS Connect & Store
- CMS EV Battery Health
- CMS Vehicle Provisioning
- CMS Vehicle Simulator

#### Automotive Cloud Developer Portal

- Add CMS Backstage Deployment.
- Add CMS Module Deployment Templates for Backstage.
- Add Proton Deployment Support.
- Add S3 Backend Support for Backstage Assets.
- Authentication and User flow implementation with Cognito.
