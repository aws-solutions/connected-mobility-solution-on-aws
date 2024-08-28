# Connected Mobility Solution on AWS - Transit Gateway Sample

## Table of Contents

- [Connected Mobility Solution on AWS - Transit Gateway Sample](#connected-mobility-solution-on-aws---transit-gateway-sample)
  - [Table of Contents](#table-of-contents)
  - [Sample Overview](#sample-overview)
  - [Deployment Instructions](#deployment-instructions)
  - [Teardown Instructions](#teardown-instructions)

## Sample Overview

This sample creates a sample setup using the CMS VPC with a Transit Gateway.
The intention of the Transit Gateway deployment is to support isolating the CMS VPC by removing the
Internet Gateway and NAT Gateways from the CMS VPC Subnets, and instead exposing all ingress and egress
internet access via a public VPC

### Known Issues

- The public VPC should have VPC endpoints without Private DNS Enabled.
And those endpoints must be added to Route53 private hosted zones to be accessible by the private VPC.
- This sample doesn't cover the pre-requisites required for cross-account Transit Gateway resource sharing and attachment

## Deployment Instructions

1. Export Required Environment Variables:

    ```bash
    export AWS_REGION="us-east-1"
    export TRANSIT_GATEWAY_STACK_NAME="cms-transit-gateway"
    export PUBLIC_VPC_STACK_NAME="cms-tgw-public-vpc"
    export PRIVATE_VPC_STACK_NAME="cms-tgw-private-vpc"
    export TRANSIT_GATEWAY_ROUTES_STACK_NAME="cms-tgw-routes"
    export PUBLIC_VPC_CIDR_PREFIX="192.168"
    export PRIVATE_VPC_CIDR_PREFIX="10.0"
    export PRIVATE_VPC_CIDR_BLOCK="${PRIVATE_VPC_CIDR_PREFIX}.0.0/16"
    ```

1. Deploy The Transit Gateway

    ```bash
    aws cloudformation create-stack --stack-name ${TRANSIT_GATEWAY_STACK_NAME} \
        --template-body file://transit-gateway.template.yaml \
        --parameters \
            ParameterKey=TransitGatewayName,ParameterValue="cms-transit-gateway"

    aws cloudformation wait stack-create-complete --stack-name "${TRANSIT_GATEWAY_STACK_NAME}"
    ```

1. Deploy a public version of the CMS VPC

    ```bash
    export TRANSIT_GATEWAY_ID=$(aws cloudformation describe-stacks --stack-name ${TRANSIT_GATEWAY_STACK_NAME} --query 'Stacks[0].Outputs[?OutputKey==`TransitGateway`].OutputValue' --output text)

    aws cloudformation create-stack --stack-name ${PUBLIC_VPC_STACK_NAME} \
    --template-body file://../../template.yaml \
    --parameters \
        ParameterKey=AllowInternetAccess,ParameterValue=true \
        ParameterKey=EnableVpcEndpoints,ParameterValue=true \
        ParameterKey=IsolatedSubnet1CIDR,ParameterValue=${PUBLIC_VPC_CIDR_PREFIX}.20.0/22 \
        ParameterKey=IsolatedSubnet2CIDR,ParameterValue=${PUBLIC_VPC_CIDR_PREFIX}.24.0/22 \
        ParameterKey=PrivateSubnet1CIDR,ParameterValue=${PUBLIC_VPC_CIDR_PREFIX}.100.0/22 \
        ParameterKey=PrivateSubnet2CIDR,ParameterValue=${PUBLIC_VPC_CIDR_PREFIX}.104.0/22 \
        ParameterKey=PublicSubnet1CIDR,ParameterValue=${PUBLIC_VPC_CIDR_PREFIX}.10.0/22 \
        ParameterKey=PublicSubnet2CIDR,ParameterValue=${PUBLIC_VPC_CIDR_PREFIX}.14.0/22 \
        ParameterKey=TransitGatewayId,ParameterValue=${TRANSIT_GATEWAY_ID} \
        ParameterKey=TransitGatewayTrafficCIDR,ParameterValue=${PRIVATE_VPC_CIDR_BLOCK} \
        ParameterKey=VpcCIDR,ParameterValue=${PUBLIC_VPC_CIDR_PREFIX}.0.0/16 \
        ParameterKey=VpcFlowLogsEnabled,ParameterValue=false \
        ParameterKey=VpcName,ParameterValue=${PUBLIC_VPC_STACK_NAME}

    aws cloudformation wait stack-create-complete --stack-name "${PUBLIC_VPC_STACK_NAME}"
    ```

1. Deploy a private version of the CMS VPC

    ```bash
    export TRANSIT_GATEWAY_ID=$(aws cloudformation describe-stacks --stack-name ${TRANSIT_GATEWAY_STACK_NAME} --query 'Stacks[0].Outputs[?OutputKey==`TransitGateway`].OutputValue' --output text)

    aws cloudformation create-stack --stack-name ${PRIVATE_VPC_STACK_NAME} \
    --template-body file://../../template.yaml \
    --parameters \
        ParameterKey=AllowInternetAccess,ParameterValue=false \
        ParameterKey=EnableVpcEndpoints,ParameterValue=false \
        ParameterKey=IsolatedSubnet1CIDR,ParameterValue=${PRIVATE_VPC_CIDR_PREFIX}.20.0/22 \
        ParameterKey=IsolatedSubnet2CIDR,ParameterValue=${PRIVATE_VPC_CIDR_PREFIX}.24.0/22 \
        ParameterKey=PrivateSubnet1CIDR,ParameterValue=${PRIVATE_VPC_CIDR_PREFIX}.100.0/22 \
        ParameterKey=PrivateSubnet2CIDR,ParameterValue=${PRIVATE_VPC_CIDR_PREFIX}.104.0/22 \
        ParameterKey=PublicSubnet1CIDR,ParameterValue=${PRIVATE_VPC_CIDR_PREFIX}.10.0/22 \
        ParameterKey=PublicSubnet2CIDR,ParameterValue=${PRIVATE_VPC_CIDR_PREFIX}.14.0/22 \
        ParameterKey=TransitGatewayId,ParameterValue=${TRANSIT_GATEWAY_ID} \
        ParameterKey=TransitGatewayTrafficCIDR,ParameterValue=0.0.0.0/0 \
        ParameterKey=VpcCIDR,ParameterValue=${PRIVATE_VPC_CIDR_BLOCK} \
        ParameterKey=VpcFlowLogsEnabled,ParameterValue=false \
        ParameterKey=VpcName,ParameterValue=${PRIVATE_VPC_STACK_NAME}

    aws cloudformation wait stack-create-complete --stack-name "${PRIVATE_VPC_STACK_NAME}"
    ```

1. Create the Transit Gateway Routes

    ```bash
    export TRANSIT_GATEWAY_ID=$(aws cloudformation describe-stacks --stack-name ${TRANSIT_GATEWAY_STACK_NAME} --query 'Stacks[0].Outputs[?OutputKey==`TransitGateway`].OutputValue' --output text)
    export PUBLIC_VPC_TRANSIT_GATEWAY_ATTACHMENT_ID=$(aws cloudformation describe-stacks --stack-name ${PUBLIC_VPC_STACK_NAME} --query 'Stacks[0].Outputs[?OutputKey==`TransitGatewayAttachment`].OutputValue' --output text)
    export PRIVATE_VPC_TRANSIT_GATEWAY_ATTACHMENT_ID=$(aws cloudformation describe-stacks --stack-name ${PRIVATE_VPC_STACK_NAME} --query 'Stacks[0].Outputs[?OutputKey==`TransitGatewayAttachment`].OutputValue' --output text)

    aws cloudformation create-stack --stack-name ${TRANSIT_GATEWAY_ROUTES_STACK_NAME} \
    --template-body file://transit-gateway-routes.template.yaml \
    --parameters \
        ParameterKey=RouteTableName,ParameterValue=${TRANSIT_GATEWAY_ROUTES_STACK_NAME} \
        ParameterKey=PrivateVpcCidr,ParameterValue=${PRIVATE_VPC_CIDR_BLOCK} \
        ParameterKey=TransitGatewayId,ParameterValue=${TRANSIT_GATEWAY_ID} \
        ParameterKey=PublicVpcTransitGatewayAttachmentId,ParameterValue=${PUBLIC_VPC_TRANSIT_GATEWAY_ATTACHMENT_ID} \
        ParameterKey=PrivateVpcTransitGatewayAttachmentId,ParameterValue=${PRIVATE_VPC_TRANSIT_GATEWAY_ATTACHMENT_ID}

    aws cloudformation wait stack-create-complete --stack-name "${TRANSIT_GATEWAY_ROUTES_STACK_NAME}"
    ```

## Teardown Instructions

NOTE: You must detach all resources from the VPCs prior to teardown or it will fail.

```bash
aws cloudformation delete-stack --stack-name "${TRANSIT_GATEWAY_ROUTES_STACK_NAME}"
aws cloudformation wait stack-delete-complete --stack-name "${TRANSIT_GATEWAY_ROUTES_STACK_NAME}"

aws cloudformation delete-stack --stack-name "${PRIVATE_VPC_STACK_NAME}"
aws cloudformation wait stack-delete-complete --stack-name "${PRIVATE_VPC_STACK_NAME}"

aws cloudformation delete-stack --stack-name "${PUBLIC_VPC_STACK_NAME}"
aws cloudformation wait stack-delete-complete --stack-name "${PUBLIC_VPC_STACK_NAME}"

aws cloudformation delete-stack --stack-name "${TRANSIT_GATEWAY_STACK_NAME}"
aws cloudformation wait stack-delete-complete --stack-name "${TRANSIT_GATEWAY_STACK_NAME}"
```
