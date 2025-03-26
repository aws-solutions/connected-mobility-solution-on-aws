# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0] - 2025-03-26

### Added

#### Automotive Cloud Developer Portal

- Add optional multi-account and multi-region deployment support to ACDP via pre-requisite guidance stacks.
- Role-based Access Control authorization added to the Backstage portal.

#### CMS

- Add CMS UI module.

## [2.0.6] - 2025-03-13

### Fixed

- Updates to resolve CVEs.

## [2.0.5] - 2025-02-25

### Fixed

- Update jsonpath-plus to resolve CVE.

## [2.0.4] - 2025-02-13

### Fixed

- Update packages to resolve CVEs.

## [2.0.3] - 2025-01-22

### Upgrade

- Upgrade from Aurora Serverless V1 to V2 since new deployments of V1 are not allowed.

### Fixed

- Configure MinLength constraint on VPC Name to prevent an issue on the AWS Console with empty strings.
- General code cleanup for unused files

## [2.0.2] - 2024-12-05

### Fixed

- Update cross-spawn to resolve CVE
- Skip tagging top-level Stack via exclude resources arg
- Separating install and upgrade functionality in make targets
- Update cms_common pre-commit target to align with package name
  in setup.py, fixing bug preventing running lib pre-commit via
  make lib-pre-commit or cd source/lib; make pre-commit
- Address pre-commit failures throughout solution
- Address SonarQube code smells
  - Defining components outside of render function (nested components)
  - Regex changes
  - Not using index as key for React components

## [2.0.1] - 2024-10-30

### Fixed

- Update http-proxy-middleware to fix CVE.

## [2.0.0] - 2024-10-23

### Added

#### All

- Add AWS MyApplications support to CloudFormation deployments via the awsApplication tag

#### Automotive Cloud Developer Portal

- Upgrade Backstage to v1.29.
- Add metrics tab to ACDP scaffolded components with monthly cost and a link to the deployment's MyApplications page.
- Add partner offerings page.

#### CMS

- Add CMS Predictive Maintenance module.

## [1.2.2] - 2024-09-26

### Fixed

- Update rollup package to resolve CVE.

## [1.2.1] - 2024-09-18

### Fixed

- Upgrade path-to-regexp to resolve CVE.
- Upgrade dset to resolve CVE.

## [1.2.0] - 2024-08-28

### Added

#### Automotive Cloud Developer Portal

- Upgrade Backstage to v1.28.
- Support for Transit Gateway attachment to the VPC.
- Support Private Hosted Zones.
- Support external DNS when not using Route53.
- Support using a custom TLS certificate uploaded to ACM.
- Add generic OAuth 2.0 support to Backstage. CMS Auth-Setup is now used to configure Backstage's IdP.
- Add CFN parameter for Backstage auth scopes.
- Add CFN parameter to set Backstage auth mode to redirect login flow instead of popup flow.

#### CMS

- Add CFN parameter to Auth Setup for callback URLs.

### Removed

#### Automotive Cloud Developer Portal

- Custom Cognito IdP for Backstage no longer needed.

## [1.1.8] - 2024-08-15

### Fixed

- Upgrade fast-xml-parser to resolve CVE.
- Upgrade axios to resolve CVE.

## [1.1.7] - 2024-07-16

### Fixed

- Upgrade inline-style-prefixer to resolve CVE.

## [1.1.6] - 2024-06-24

### Fixed

- Upgrade ws to resolve CVE.

## [1.1.5] - 2024-06-17

### Fixed

- Upgrade braces to resolve CVE.
- Update README instructions to run Backstage locally.

## [1.1.4] - 2024-06-06

### Fixed

- Upgrade mysql to resolve CVE.
- Fix integration test issue by allowing cron to be supplied to FleetWise Glue Job.

## [1.1.3] - 2024-05-16

### Fixed

- Upgrade werkzeug to resolve CVE.

## [1.1.2] - 2024-04-30

### Fixed

- Upgrade formidable to resolve CVE.
- Upgrade mysql2 to resolve CVE.

## [1.1.1] - 2024-04-18

### Fixed

- Upgrade mysql2 to resolve CVE.
- Upgrade requests library with idna peer dependency to resolve pip-audit.
- Upgrade @backstage/cli to resolve Jest errors.
- Pin moto version in Alerts module to avoid moto Athena bug introduced in moto 5.0.3.

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
