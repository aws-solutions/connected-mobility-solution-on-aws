# Automotive Cloud Developer Portal - Multi-Account, Multi-Region Setup

## Table of Contents

- [Automotive Cloud Developer Portal - Multi-Account, Multi-Region Setup](#automotive-cloud-developer-portal---multi-account-multi-region-setup)
  - [Table of Contents](#table-of-contents)
  - [Guidance Overview](#guidance-overview)
  - [Architecture Diagram](#architecture-diagram)
  - [Deployment Instructions](#deployment-instructions)
  - [Teardown Instructions](#teardown-instructions)

## Guidance Overview

This guidance provide CloudFormation templates that instantiates roles necessary for ACDP to perform
cross-account deployments and recognize available accounts for deployement through AWS Organizations.
There are two CloudFormation templates in this guidance.

1. ou_arn_list_macro.template.yaml:

    This template deploys an AWS Transform macro function that is used in the second template
    to modify the template at runtime.

1. acdp_multi_acct_setup.template.yaml:

    This template deploys roles and CloudFormation StackSet in AWS Organization Root Account.

## Architecture Diagram

![Architecture Diagram](../documentation/architecture/acdp-multi-acct-setup-guidance-architecture.svg)

## Deployment Instructions

1. Add multi account guidance rc variables to .cmsrc file and source environment variables:

    ```bash
    make add-ma-vars-to-rc-file
    source .cmsrc
    ```

1. Deploy the OuArnList Transform Macro Stack:

    ```bash
    make deploy-multi-account-guidance-macro
    ```

1. Deploy the ACDP Multi Acct Setup Stack:

    ```bash
    make deploy-multi-account-guidance
    ```

## Teardown Instructions

1. Delete the ACDP Multi Acct Setup Stack:

    ```bash
    make destroy-multi-account-guidance
    ```

1. Delete the OuArnList Transform Macro Stack:

    ```bash
    make destroy-multi-account-guidance-macro
    ```
