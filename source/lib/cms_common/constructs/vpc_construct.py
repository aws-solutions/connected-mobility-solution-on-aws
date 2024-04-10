# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from typing import Any, Dict, List

# Third Party Libraries
import jsii
from attrs import define

# AWS Libraries
from aws_cdk import Annotations, CustomResource, Stack, aws_ec2, aws_iam
from constructs import Construct

# Connected Mobility Solution on AWS
from ..config.resource_names import ResourceName
from ..config.ssm import resolve_ssm_parameter
from ..enums.aws_resource_lookup import AwsResourceLookupCustomResourceType
from ..resource_names.config import ConfigResourceNames


def get_vpc_name(scope: Construct, app_unique_id: str) -> str:
    config_resource_names = ConfigResourceNames.from_app_unique_id(app_unique_id)

    aws_resource_lookup_lambda_arn = resolve_ssm_parameter(
        parameter_name=config_resource_names.aws_resource_lookup_lambda_arn_ssm_parameter
    )

    vpc_name_custom_resource = CustomResource(
        scope,
        "vpc-name-custom-resource",
        service_token=aws_resource_lookup_lambda_arn,
        resource_type=f"Custom::{AwsResourceLookupCustomResourceType.SSM_PARAMETERS.value}",
        properties={
            "Resource": AwsResourceLookupCustomResourceType.SSM_PARAMETERS.value,
            "ParameterName": config_resource_names.vpc_name_ssm_parameter,
        },
    )

    return vpc_name_custom_resource.get_att_string("parameter_value")


@define(auto_attribs=True, frozen=True)
class VpcConfig:
    vpc_name: str
    vpc_id: str
    public_subnets: List[str]
    private_subnets: List[str]
    isolated_subnets: List[str]
    availability_zones: List[str]


def create_vpc_config(vpc_name: str) -> VpcConfig:
    vpc_ssm_prefix = f"/solution/vpc/{vpc_name}"
    return VpcConfig(
        vpc_name=vpc_name,
        vpc_id=resolve_ssm_parameter(
            parameter_name=ResourceName.slash_separated(
                prefix=vpc_ssm_prefix, name="vpcid"
            )
        ),
        public_subnets=[
            resolve_ssm_parameter(
                parameter_name=ResourceName.slash_separated(
                    prefix=vpc_ssm_prefix, name="subnets/public/1"
                )
            ),
            resolve_ssm_parameter(
                parameter_name=ResourceName.slash_separated(
                    prefix=vpc_ssm_prefix, name="subnets/public/2"
                )
            ),
        ],
        private_subnets=[
            resolve_ssm_parameter(
                parameter_name=ResourceName.slash_separated(
                    prefix=vpc_ssm_prefix, name="subnets/private/1"
                )
            ),
            resolve_ssm_parameter(
                parameter_name=ResourceName.slash_separated(
                    prefix=vpc_ssm_prefix, name="subnets/private/2"
                )
            ),
        ],
        isolated_subnets=[
            resolve_ssm_parameter(
                parameter_name=ResourceName.slash_separated(
                    prefix=vpc_ssm_prefix, name="subnets/isolated/1"
                )
            ),
            resolve_ssm_parameter(
                parameter_name=ResourceName.slash_separated(
                    prefix=vpc_ssm_prefix, name="subnets/isolated/2"
                )
            ),
        ],
        availability_zones=[
            resolve_ssm_parameter(
                parameter_name=ResourceName.slash_separated(
                    prefix=vpc_ssm_prefix, name="azs/1"
                )
            ),
            resolve_ssm_parameter(
                parameter_name=ResourceName.slash_separated(
                    prefix=vpc_ssm_prefix, name="azs/2"
                )
            ),
        ],
    )


class IncorrectSubnetType(Exception):
    ...


@jsii.implements(aws_ec2.IVpc)
class UnsafeDynamicVpc(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        vpc_id: str,
        vpc_name: str,
        public_subnets: List[aws_ec2.ISubnet],
        private_subnets: List[aws_ec2.ISubnet],
        isolated_subnets: List[aws_ec2.ISubnet],
        availability_zones: List[str],
    ) -> None:
        super().__init__(scope, construct_id)
        self._vpc_id = vpc_id
        self._vpc_name = vpc_name
        self._vpc_arn = Stack.of(self).format_arn(
            service="ec2", resource="vpc", resource_name=self.vpc_id
        )

        self._public_subnets = public_subnets
        self._private_subnets = private_subnets
        self._isolated_subnets = isolated_subnets
        self._availability_zones = availability_zones

    @property
    def vpc_id(self) -> str:
        return self._vpc_id

    @property
    def availability_zones(self) -> List[str]:
        return self._availability_zones

    @property
    def public_subnets(self) -> List[aws_ec2.ISubnet]:
        return self._public_subnets

    @property
    def private_subnets(self) -> List[aws_ec2.ISubnet]:
        return self._private_subnets

    @property
    def isolated_subnets(self) -> List[aws_ec2.ISubnet]:
        return self._isolated_subnets

    @property
    def vpc_arn(self) -> str:
        return self._vpc_arn

    def select_subnets(self, selection: aws_ec2.SubnetSelection) -> Dict[str, Any]:
        ### As of now this function only supports selection of subnet by types
        selected_subnets = None

        has_public = False
        match (selection.subnet_type):
            case aws_ec2.SubnetType.PUBLIC:
                selected_subnets = self._public_subnets
                has_public = True
            case aws_ec2.SubnetType.PRIVATE_WITH_EGRESS:
                selected_subnets = self._private_subnets
            case aws_ec2.SubnetType.PRIVATE_ISOLATED:
                selected_subnets = self._isolated_subnets

        if not selected_subnets:
            raise IncorrectSubnetType

        internet_connectivity_established = aws_iam.CompositeDependable(
            *[subnet.internet_connectivity_established for subnet in selected_subnets]
        )
        return {
            "subnetIds": [subnet.subnet_id for subnet in selected_subnets],
            "availabilityZones": self._availability_zones,
            "hasPublic": has_public,
            "subnets": selected_subnets,
            "internetConnectivityEstablished": internet_connectivity_established,
        }


class VpcConstruct(Construct):
    def __init__(
        self, scope: Construct, construct_id: str, vpc_config: VpcConfig
    ) -> None:
        super().__init__(scope, construct_id)

        self.public_subnets = [
            aws_ec2.Subnet.from_subnet_attributes(
                self,
                "public-subnet-1",
                subnet_id=vpc_config.public_subnets[0],
            ),
            aws_ec2.Subnet.from_subnet_attributes(
                self,
                "public-subnet-2",
                subnet_id=vpc_config.public_subnets[1],
            ),
        ]
        Annotations.of(self.public_subnets[0]).acknowledge_warning(
            "@aws-cdk/aws-ec2:noSubnetRouteTableId"
        )
        Annotations.of(self.public_subnets[1]).acknowledge_warning(
            "@aws-cdk/aws-ec2:noSubnetRouteTableId"
        )

        self.public_subnet_selection = aws_ec2.SubnetSelection(
            subnets=self.public_subnets, subnet_type=aws_ec2.SubnetType.PUBLIC
        )

        self.private_subnets = [
            aws_ec2.Subnet.from_subnet_attributes(
                self,
                "private-subnet-1",
                subnet_id=vpc_config.private_subnets[0],
            ),
            aws_ec2.Subnet.from_subnet_attributes(
                self,
                "private-subnet-2",
                subnet_id=vpc_config.private_subnets[1],
            ),
        ]
        Annotations.of(self.private_subnets[0]).acknowledge_warning(
            "@aws-cdk/aws-ec2:noSubnetRouteTableId"
        )
        Annotations.of(self.private_subnets[1]).acknowledge_warning(
            "@aws-cdk/aws-ec2:noSubnetRouteTableId"
        )

        self.private_subnet_selection = aws_ec2.SubnetSelection(
            subnets=self.private_subnets,
            subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS,
        )

        self.isolated_subnets = [
            aws_ec2.Subnet.from_subnet_attributes(
                self,
                "isolated-subnet-1",
                subnet_id=vpc_config.isolated_subnets[0],
            ),
            aws_ec2.Subnet.from_subnet_attributes(
                self,
                "isolated-subnet-2",
                subnet_id=vpc_config.isolated_subnets[1],
            ),
        ]
        Annotations.of(self.isolated_subnets[0]).acknowledge_warning(
            "@aws-cdk/aws-ec2:noSubnetRouteTableId"
        )
        Annotations.of(self.isolated_subnets[1]).acknowledge_warning(
            "@aws-cdk/aws-ec2:noSubnetRouteTableId"
        )

        self.isolated_subnet_selection = aws_ec2.SubnetSelection(
            subnets=self.isolated_subnets,
            subnet_type=aws_ec2.SubnetType.PRIVATE_ISOLATED,
        )

        self.vpc = UnsafeDynamicVpc(
            self,
            "cms-vpc",
            vpc_id=vpc_config.vpc_id,
            vpc_name=vpc_config.vpc_name,
            public_subnets=self.public_subnets,
            private_subnets=self.private_subnets,
            isolated_subnets=self.isolated_subnets,
            availability_zones=vpc_config.availability_zones,
        )
