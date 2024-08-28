# Deployment Scenarios for ACDP

- [Deployment Scenarios for ACDP](#deployment-scenarios-for-acdp)
  - [Introduction](#introduction)
    - [Overview](#overview)
  - [Deployment Scenarios](#deployment-scenarios)
    - [Scenario 1: Fully Public with Route53](#scenario-1-fully-public-with-route53)
      - [Description](#description)
      - [Diagram](#diagram)
      - [Steps](#steps)
    - [Scenario 2: Fully Public with an External DNS + Custom Certificate](#scenario-2-fully-public-with-an-external-dns--custom-certificate)
      - [Description](#description-1)
      - [Diagram](#diagram-1)
      - [Steps](#steps-1)
    - [Scenario 3: Public DNS, Private Endpoint](#scenario-3-public-dns-private-endpoint)
      - [Description](#description-2)
      - [Diagram](#diagram-2)
      - [Steps](#steps-2)
    - [Scenario 4: Private Route53, Internal Only Access](#scenario-4-private-route53-internal-only-access)
      - [Description](#description-3)
      - [Diagram](#diagram-3)
      - [Steps](#steps-3)
    - [Scenario 5: Private VPC Linked to Public VPC via TGW](#scenario-5-private-vpc-linked-to-public-vpc-via-tgw)
      - [Description](#description-4)
      - [Diagram](#diagram-4)
      - [Steps](#steps-4)

## Introduction

### Overview

This guide provides detailed deployment scenarios for different network topologies supported by the CMS VPC and ACDP/Backstage

## Deployment Scenarios

### Scenario 1: Fully Public with Route53

#### Description

In this scenario, ACDP is deployed within a public VPC with a public hosted zone managed by Route53
and an auto-generated public certificate.

#### Diagram

![Public Deployment](acdp-public.svg)

#### Steps

1. Deploy the public VPC.

    ```url
    https://us-east-1.console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/create/review
    ?templateURL=https://s3.amazonaws.com/solutions-reference/connected-mobility-solution-on-aws/latest/vpc/vpc.template
    &stackName=acdp-public-vpc
    &param_VpcName=acdp-public-vpc
    &param_VpcFlowLogsEnabled=false
    &param_AllowInternetAccess=true
    &param_EnableVpcEndpoints=true
    ```

1. Configure Route53 with a public hosted zone.
1. Deploy ACDP.

    ```url
    https://us-east-1.console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/create/review
    ?templateURL=https://s3.amazonaws.com/solutions-reference/connected-mobility-solution-on-aws/latest/acdp/acdp.template
    &stackName=acdp-public
    &param_AcdpUniqueId=acdp-public
    &param_VpcName=acdp-public-vpc
    &param_Route53HostedZoneId=<ROUTE53_PUBLIC_HZ_ID>
    &param_FullyQualifiedDomainName=<DOMAIN_FOR_BACkSTAGE>
    &param_IsPublicFacing=true
    ```

### Scenario 2: Fully Public with an External DNS + Custom Certificate

![Public Deployment w/ External DNS + Custom Certificate](acdp-public-ext-dns.svg)

#### Description

The network topology is the following:

1. A Public VPC is deployed. The VPC has an Internet Gateway and NAT Gateways configured.
1. A Public Hosted Zone is created in a DNS Provider
1. An ACM Certificate is provided by the deployer for the FQDN specified in the ACDP deployment parameters
1. ACDP/Backstage is deployed with an ALB in the public subnet of the VPC

This scenario involves deploying ACDP within a public VPC with a public hosted zone managed
by an External DNS Provider and a custom public certificate.

Note that in this scenario, the Route53HostedZoneId parameter is not set.

#### Diagram

![Public Deployment](acdp-public.svg)

#### Steps

1. Deploy the public VPC.

    ```url
    https://us-east-1.console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/create/review
    ?templateURL=https://s3.amazonaws.com/solutions-reference/connected-mobility-solution-on-aws/latest/vpc/vpc.template
    &stackName=acdp-public-vpc
    &param_VpcName=acdp-public-vpc
    &param_VpcFlowLogsEnabled=false
    &param_AllowInternetAccess=true
    &param_EnableVpcEndpoints=true
    ```

1. Configure a FQDN in the external DNS provider. Store the FQDN.
1. Create and Import a TLS v1.3 compatible certificate to ACM. Store the ARN of the Certificate
1. Deploy ACDP.

    ```url
    https://us-east-1.console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/create/review
    ?templateURL=https://s3.amazonaws.com/solutions-reference/connected-mobility-solution-on-aws/latest/acdp/acdp.template
    &stackName=acdp-public-external-dns
    &param_AcdpUniqueId=acdp-ext-dns
    &param_VpcName=acdp-public-vpc
    &param_FullyQualifiedDomainName=<DOMAIN_FOR_BACkSTAGE>
    &param_CustomAcmCertificateArn=<ACM_CERT_ARN_FOR_DOMAIN>
    &param_IsPublicFacing=true
    ```

### Scenario 3: Public DNS, Private Endpoint

#### Description

In this scenario, ACDP is deployed within a public VPC with a public hosted zone managed by Route53,
but incoming access is restricted to peered networks only or an internet facing reverse proxy
in the public subnet of the VPC.

#### Diagram

![Public DNS - Private Endpoint Deployment](acdp-public-dns-private-endpoint.svg)

#### Steps

1. Deploy the public VPC.

    ```url
    https://us-east-1.console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/create/review
    ?templateURL=https://s3.amazonaws.com/solutions-reference/connected-mobility-solution-on-aws/latest/vpc/vpc.template
    &stackName=acdp-public-vpc
    &param_VpcName=acdp-public-vpc
    &param_VpcFlowLogsEnabled=false
    &param_AllowInternetAccess=true
    &param_EnableVpcEndpoints=true
    ```

1. Configure Route53 with a public hosted zone.
1. Deploy ACDP.

    ```url
    https://us-east-1.console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/create/review
    ?templateURL=https://s3.amazonaws.com/solutions-reference/connected-mobility-solution-on-aws/latest/acdp/acdp.template
    &stackName=acdp-public-external-dns
    &param_AcdpUniqueId=acdp-ext-dns
    &param_VpcName=acdp-public-vpc
    &param_Route53HostedZoneId=<ROUTE53_PUBLIC_HZ_ID>
    &param_FullyQualifiedDomainName=<DOMAIN_FOR_BACkSTAGE>
    &param_IsPublicFacing=false
    ```

### Scenario 4: Private Route53, Internal Only Access

#### Description

This scenario involves deploying ACDP within a private VPC with a private hosted zone managed by Route53
and an internal ALB.

#### Diagram

![Private Deployment](./acdp-private.svg)

#### Steps

1. Setup Public and Private VPCs with Transit Gateway Attachments.
   1. Follow this guide for a sample configuration: [TGW Network Sample](../../../source/modules/vpc/source/samples/transit-gateway/README.md)
   1. If you want to use an existing public VPC and transit gateway, only deploy the private VPC and set up a TGW attachment.

    ```url
        https://us-east-1.console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/create/review
    ?templateURL=https://s3.amazonaws.com/solutions-reference/connected-mobility-solution-on-aws/latest/vpc/vpc.template
    &stackName=acdp-private-vpc
    &param_VpcName=acdp-public-vpc
    &param_VpcFlowLogsEnabled=false
    &param_AllowInternetAccess=false
    &param_EnableVpcEndpoints=false
    &param_TransitGatewayId=<TGW_ID>
    &param_TransitGatewayTrafficCIDR=0.0.0.0/0
    ```

1. Configure Route53 with a private hosted zone. Attach the hosted zone to both the public and private VPCs.
1. Configure a self-signed certificate and import it to ACM.
1. Deploy ACDP into the private VPC

    ```url
    https://us-east-1.console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/create/review
    ?templateURL=https://s3.amazonaws.com/solutions-reference/connected-mobility-solution-on-aws/latest/acdp/acdp.template
    &stackName=acdp-private
    &param_AcdpUniqueId=acdp-private
    &param_VpcName=acdp-private-vpc
    &param_Route53HostedZoneId=<ROUTE53_PRIVATE_HZ_ID>
    &param_FullyQualifiedDomainName=<DOMAIN_FOR_BACkSTAGE>
    &param_IsPublicFacing=false
    ```

1. Set up either an enterprise network attachment or an ALB in the public VPC to act as a reverse proxy to
the internal ALB created by the ACDP deployment.

### Scenario 5: Private VPC Linked to Public VPC via TGW

#### Description

In this scenario, ACDP is deployed within a private VPC that is linked to a public VPC using a Transit Gateway (TGW).

#### Diagram

![Private Deployment w/ TGW](./acdp-private-with-tgw.svg)

#### Steps

1. Setup Public and Private VPCs with Transit Gateway Attachments.
   1. Follow this guide for a sample configuration: [TGW Network Sample](../../../source/modules/vpc/source/samples/transit-gateway/README.md)
   1. If you want to use an existing public VPC and transit gateway, only deploy the private VPC and set up a TGW attachment.

    ```url
        https://us-east-1.console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/create/review
    ?templateURL=https://s3.amazonaws.com/solutions-reference/connected-mobility-solution-on-aws/latest/vpc/vpc.template
    &stackName=acdp-private-vpc
    &param_VpcName=acdp-public-vpc
    &param_VpcFlowLogsEnabled=false
    &param_AllowInternetAccess=false
    &param_EnableVpcEndpoints=false
    &param_TransitGatewayId=<TGW_ID>
    &param_TransitGatewayTrafficCIDR=0.0.0.0/0
    ```

1. Configure Route53 with a private hosted zone. Attach the hosted zone to both the public and private VPCs.
1. Configure a self-signed certificate and import it to ACM.
1. Deploy ACDP into the private VPC

    ```url
    https://us-east-1.console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/create/review
    ?templateURL=https://s3.amazonaws.com/solutions-reference/connected-mobility-solution-on-aws/latest/acdp/acdp.template
    &stackName=acdp-private
    &param_AcdpUniqueId=acdp-private
    &param_VpcName=acdp-private-vpc
    &param_Route53HostedZoneId=<ROUTE53_PRIVATE_HZ_ID>
    &param_FullyQualifiedDomainName=<DOMAIN_FOR_BACkSTAGE>
    &param_IsPublicFacing=false
    ```

1. Set up either an enterprise network attachment or an ALB in the public VPC to act as a reverse proxy to
the internal ALB created by the ACDP deployment.
