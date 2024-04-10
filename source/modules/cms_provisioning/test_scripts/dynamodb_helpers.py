# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import os
import uuid
from functools import lru_cache
from typing import TYPE_CHECKING, List

# AWS Libraries
import boto3

if TYPE_CHECKING:
    # Third Party Libraries
    from mypy_boto3_cloudformation.client import CloudFormationClient
    from mypy_boto3_dynamodb.client import DynamoDBClient
else:
    DynamoDBClient = object
    CloudFormationClient = object


@lru_cache(maxsize=128)
def get_dynamodb_client() -> DynamoDBClient:
    return boto3.client("dynamodb", region_name=os.environ["AWS_REGION"])


@lru_cache(maxsize=128)
def get_cloudformation_client() -> CloudFormationClient:
    return boto3.client("cloudformation", region_name=os.environ["AWS_REGION"])


def create_random_authorized_vehicles(num_vehicles: int) -> List[str]:
    # add vehicles to dynamodb table
    vins = []
    authorized_vehicles_table_name = get_authorized_vehicles_table_name()
    for _ in range(num_vehicles):
        vin = "".join(str(uuid.uuid4()).split("-"))
        add_vehicle_to_authorized_vehicles_table(
            vin=vin, table_name=authorized_vehicles_table_name
        )
        vins.append(vin)
    print(f"Created {num_vehicles} vehicles.")
    return vins


def get_authorized_vehicles_table_name() -> str:
    stacks = get_cloudformation_client().list_stacks(
        StackStatusFilter=["CREATE_COMPLETE"]
    )["StackSummaries"]
    stack_name = [
        stack["StackName"]
        for stack in stacks
        if "cms-provisioning" in stack["StackName"]
    ][0]
    stack_resources = get_cloudformation_client().list_stack_resources(
        StackName=stack_name
    )["StackResourceSummaries"]
    ddb_resources = [
        resource
        for resource in stack_resources
        if resource["ResourceType"] == "AWS::DynamoDB::Table"
    ]
    authorized_vehicles_table_name = [
        resource["PhysicalResourceId"]
        for resource in ddb_resources
        if "authorized" in resource["PhysicalResourceId"]
    ][0]
    return authorized_vehicles_table_name


def add_vehicle_to_authorized_vehicles_table(vin: str, table_name: str) -> None:
    get_dynamodb_client().put_item(
        TableName=table_name,
        Item={
            "vin": {"S": vin},
            "make": {"S": "McLaren"},
            "model": {"S": "Senna"},
            "year": {"S": "2022"},
            "allow_provisioning": {"BOOL": True},
        },
    )
