# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.4] - 2024-02-28

### Fixed

- Upgrade backstage to 1.23.3 to mitigate vulnerability
- Fix a bug that could occur if the s3 version of the backstage source was prefixed with a special character.


## [1.0.3] - 2024-02-23

### Fixed

- Added resolution for the ECDSA package to mitigate vulnerability
- Added resolution for the cyrptography package to mitigate vulnerability
- Added resolution for node-ip package to mitigate vulnerability


## [1.0.2] - 2024-01-10

### Fixed

- Updated Grafana workspace in EV Battery Health module to include
plugin management and install Amazon Athena plugin
- Added resolution for octokit package to mitigate vulnerability
- Added resolution for follow-redirects package to mitigate vulnerability
- Added resolution for swagger-ui-react package to address Backstage build failure
- Removed `yarn tsc:full` from backstage image build
- Add ignore pattern for Axios in vehicle simulator to ensure correct version usage

## [1.0.1] - 2023-11-15

### Fixed

- Updated various README URLs to the correct values
- Resolved an issue where the Aurora PostgresSQL cluster's version defaulted to 11 instead of 13 in some regions
- Pinned Node and Python versions in Proton manifest.yml for every module

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

- CMS Backstage Deployment
- CMS Module Deployment Templates for Backstage
- Proton Deployment Support
- S3 Backend Support for Backstage Assets
- Authentication and User flow implementation with Cognito
