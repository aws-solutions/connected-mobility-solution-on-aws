# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
