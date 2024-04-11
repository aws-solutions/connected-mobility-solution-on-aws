# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import json
import os
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Dict, Generator

# AWS Libraries
import boto3
from aws_lambda_powertools import Logger
from botocore.config import Config
from botocore.exceptions import ClientError

if TYPE_CHECKING:
    # Third Party Libraries
    from mypy_boto3_iot.client import IoTClient
    from mypy_boto3_resourcegroupstaggingapi.client import (
        ResourceGroupsTaggingAPIClient,
    )
    from mypy_boto3_secretsmanager.client import SecretsManagerClient

else:
    IoTClient = object
    SecretsManagerClient = object
    ResourceGroupsTaggingAPIClient = object

logger = Logger()


class DeviceProvisioner:
    def __init__(
        self,
        aws_account_id: str,
        aws_region: str,
        simulation_id: str,
        user_agent_string: str,
    ) -> None:
        self.aws_account_id = aws_account_id
        self.aws_region = aws_region
        self.simulation_id = simulation_id
        self.user_agent_string = user_agent_string

    @lru_cache(128)
    def iot_client(self) -> IoTClient:
        return boto3.client(
            "iot", config=Config(user_agent_extra=self.user_agent_string)
        )

    @lru_cache(128)
    def secret_manager_client(self) -> SecretsManagerClient:
        return boto3.client(
            "secretsmanager", config=Config(user_agent_extra=self.user_agent_string)
        )

    @lru_cache(128)
    def tagging_client(self) -> ResourceGroupsTaggingAPIClient:
        return boto3.client(
            "resourcegroupstaggingapi",
            config=Config(user_agent_extra=self.user_agent_string),
        )

    def create_device_secrets(self, device_name: str) -> Dict[str, Any]:
        try:
            keys_and_cert = self.iot_client().create_keys_and_certificate()
            secret = self.secret_manager_client().create_secret(
                Name=f"vs-device/{device_name}-secret",
                Description=f"Keys and certificate for device {device_name} connecting to iot-core",
                SecretString=json.dumps(keys_and_cert),
                Tags=[{"Key": "cms-simulated-vehicle", "Value": self.simulation_id}],
            )

            logger.info("created secrets for device: %s", device_name)

        except ClientError as err:
            logger.error(
                "Error creating device secrets for %s. Here's why: %s: %s",
                device_name,
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
                exc_info=True,
            )
            raise

        return {
            "keys": keys_and_cert,
            "secret": secret,
        }

    def create_thing(self, device_name: str, certificate_arn: str) -> Dict[str, Any]:
        try:
            thing = self.iot_client().create_thing(
                thingName=device_name,
                attributePayload={
                    "attributes": {
                        "simulation_id": self.simulation_id,
                    }
                },
            )

            self.iot_client().add_thing_to_thing_group(
                thingName=device_name,
                thingGroupName=os.environ.get("SIMULATOR_THING_GROUP_NAME", ""),
            )

            self.iot_client().attach_thing_principal(
                thingName=device_name,
                principal=certificate_arn,
            )

            device_policy = self.iot_client().create_policy(
                policyName=f"{device_name}-policy",
                policyDocument=json.dumps(
                    {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Effect": "Allow",
                                "Action": "iot:Publish",
                                "Resource": f"arn:aws:iot:{self.aws_region}:{self.aws_account_id}:topic/{os.environ.get('TOPIC_PREFIX', 'cms/data/simulated')}/{device_name}",
                            },
                        ],
                    }
                ),
            )

            self.iot_client().attach_policy(
                policyName=device_policy["policyName"],
                target=certificate_arn,
            )

            thing_info = {
                "thing": thing,
                "policy": device_policy,
            }

            logger.info("created thing: %s", device_name, extra=thing_info)

        except ClientError as err:
            logger.error(
                "Error creating thing for %s. Here's why: %s: %s",
                device_name,
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
                exc_info=True,
            )
            raise

        return thing_info

    def get_simulated_secrets(self) -> Generator[str, None, None]:
        get_resources_iterator = (
            self.tagging_client()
            .get_paginator("get_resources")
            .paginate(
                TagFilters=[
                    {
                        "Key": "cms-simulated-vehicle",
                        "Values": [
                            self.simulation_id,
                        ],
                    },
                ],
                ResourceTypeFilters=[
                    "secretsmanager:secret",
                ],
            )
        )

        for page in get_resources_iterator:
            for resource in page["ResourceTagMappingList"]:
                yield resource["ResourceARN"]

    def get_simulated_things(self) -> Generator[Dict[str, Any], None, None]:
        list_things_iterator = (
            self.iot_client()
            .get_paginator("list_things")
            .paginate(
                attributeName="simulation_id",
                attributeValue=self.simulation_id,
                usePrefixAttributeValue=True,
            )
        )

        for page in list_things_iterator:
            for thing in page["things"]:
                yield dict(thing)

    def delete_iot_thing(self, thing_name: str) -> None:
        try:
            principals = self.iot_client().list_thing_principals(thingName=thing_name)
            for principal in principals["principals"]:
                self.iot_client().detach_thing_principal(
                    principal=principal, thingName=thing_name
                )
                self.delete_iot_principal(principal)

            self.iot_client().delete_thing(thingName=thing_name)

            logger.info(
                "deleted provisioned thing: %s",
                thing_name,
            )

        except ClientError as err:
            logger.error(
                "Error deleting thing %s. Here's why: %s: %s",
                thing_name,
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
                exc_info=True,
            )
            raise

    def delete_iot_principal(self, principal: str) -> None:
        try:
            certificate_id = principal.split("/")[-1]
            policies = self.iot_client().list_principal_policies(principal=principal)
            for policy in policies["policies"]:
                self.iot_client().detach_policy(
                    policyName=policy["policyName"], target=principal
                )
                self.delete_iot_policy(policy["policyName"])

            self.iot_client().delete_certificate(certificateId=certificate_id)

            logger.info(
                "deleted principal: %s",
                principal,
            )

        except ClientError as err:
            logger.error(
                "Error deleting principal %s. Here's why: %s: %s",
                principal,
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
                exc_info=True,
            )
            raise

    def delete_iot_policy(self, policy_name: str) -> None:
        try:
            self.iot_client().delete_policy(policyName=policy_name)

            logger.info(
                "deleted policy: %s",
                policy_name,
            )

        except ClientError as err:
            logger.error(
                "Error deleting policy %s. Here's why: %s: %s",
                policy_name,
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
                exc_info=True,
            )
            raise

    def delete_secretsmanager_secret(self, secret_arn: str) -> None:
        try:
            self.secret_manager_client().delete_secret(
                SecretId=secret_arn, ForceDeleteWithoutRecovery=True
            )

            logger.info("deleted provisioned secret: %s", secret_arn)

        except ClientError as err:
            logger.error(
                "Error deleting secret %s. Here's why: %s: %s",
                secret_arn,
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
                exc_info=True,
            )
            raise
