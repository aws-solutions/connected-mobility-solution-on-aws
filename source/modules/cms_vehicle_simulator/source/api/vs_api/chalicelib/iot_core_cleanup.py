# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import os
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Dict, Generator

# AWS Libraries
import boto3
from botocore.config import Config

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


class IotCoreCleanup:
    @lru_cache(128)
    def iot_client(self) -> IoTClient:
        return boto3.client(
            "iot", config=Config(user_agent_extra=os.environ["USER_AGENT_STRING"])
        )

    @lru_cache(128)
    def secret_manager_client(self) -> SecretsManagerClient:
        return boto3.client(
            "secretsmanager",
            config=Config(user_agent_extra=os.environ["USER_AGENT_STRING"]),
        )

    @lru_cache(128)
    def tagging_client(self) -> ResourceGroupsTaggingAPIClient:
        return boto3.client(
            "resourcegroupstaggingapi",
            config=Config(user_agent_extra=os.environ["USER_AGENT_STRING"]),
        )

    def get_simulated_secrets(self, simulation_id: str) -> Generator[str, None, None]:
        get_resources_iterator = (
            self.tagging_client()
            .get_paginator("get_resources")
            .paginate(
                TagFilters=[
                    {"Key": "cms-simulated-vehicle", "Values": [f"{simulation_id}"]},
                ],
                ResourceTypeFilters=[
                    "secretsmanager:secret",
                ],
            )
        )

        for page in get_resources_iterator:
            for resource in page["ResourceTagMappingList"]:
                yield resource["ResourceARN"]

    def get_simulated_things(
        self, simulation_id: str
    ) -> Generator[Dict[str, Any], None, None]:
        list_things_iterator = self.iot_client().get_paginator("list_things")

        for page in list_things_iterator.paginate():
            for thing in page["things"]:  # pylint: disable=W0621
                if thing["attributes"].get("simulation_id", None) == simulation_id:
                    yield thing  # type: ignore

    def delete_secretsmanager_secret(
        self, secret_arn: str
    ) -> None:  # pylint: disable=W0621
        self.secret_manager_client().delete_secret(
            SecretId=secret_arn, ForceDeleteWithoutRecovery=True
        )

    def delete_iot_thing(self, thing_name: str) -> None:
        principals = self.iot_client().list_thing_principals(thingName=thing_name)
        for principal in principals["principals"]:
            self.detach_thing_principal(principal=principal, thing_name=thing_name)
            if principal.split("/")[0].split(":")[-1] == "cert":
                self.iot_client().delete_certificate(
                    certificateId=principal.split("/")[-1]
                )

        self.iot_client().delete_thing(thingName=thing_name)

    def detach_thing_principal(self, principal: str, thing_name: str) -> None:
        policies = self.iot_client().list_attached_policies(target=principal)
        for policy in policies["policies"]:
            self.delete_iot_policy(policy["policyName"], principal)

        self.iot_client().detach_thing_principal(
            thingName=thing_name, principal=principal
        )

    def delete_iot_policy(self, policy_name: str, principal: str) -> None:
        self.iot_client().detach_policy(policyName=policy_name, target=principal)
        self.iot_client().delete_policy(policyName=policy_name)

    def cleanup(self, simulation_id: str) -> None:
        for secret_arn in self.get_simulated_secrets(simulation_id=simulation_id):
            self.delete_secretsmanager_secret(secret_arn)

        for thing in self.get_simulated_things(simulation_id=simulation_id):
            self.delete_iot_thing(thing["thingName"])
