# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import os
from typing import Generator

# AWS Libraries
import boto3

AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_SESSION_TOKEN = os.environ.get("AWS_SESSION_TOKEN")
PROFILE = None

if not all([AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN]):
    PROFILE = os.environ.get(
        "AWS_PROFILE",
        input(f"Which AWS profile {boto3.session.Session().available_profiles}: "),
    )

session = boto3.Session(profile_name=PROFILE)
tagging_client = session.client("resourcegroupstaggingapi")
secretsmanager_client = session.client("secretsmanager")
iot_client = session.client("iot")


def get_simulated_secrets() -> Generator[str, None, None]:
    get_resources_iterator = tagging_client.get_paginator("get_resources").paginate(
        TagFilters=[
            {
                "Key": "cms-simulated-vehicle",
            },
        ],
        ResourceTypeFilters=[
            "secretsmanager:secret",
        ],
    )

    for page in get_resources_iterator:
        for resource in page["ResourceTagMappingList"]:
            yield resource["ResourceARN"]


def get_simulated_things() -> Generator[str, None, None]:
    list_things_iterator = iot_client.get_paginator(
        "list_things_in_thing_group",
    )
    parameters = {"thingGroupName": "cms-simulated-vehicle"}

    for page in list_things_iterator.paginate(**parameters):  # type: ignore
        yield from page["things"]  # pylint: disable=redefined-outer-name


def delete_secretsmanager_secret(
    secret_arn: str,  # pylint: disable=redefined-outer-name
) -> None:
    secretsmanager_client.delete_secret(
        SecretId=secret_arn, ForceDeleteWithoutRecovery=True
    )
    print(f"deleted secret: {secret_arn}")


def delete_iot_thing(thing_name: str) -> None:
    principals = iot_client.list_thing_principals(thingName=thing_name)
    for principal in principals["principals"]:
        detach_thing_principal(principal=principal, thing_name=thing_name)
        if principal.split("/")[0].split(":")[-1] == "cert":
            iot_client.delete_certificate(certificateId=principal.split("/")[-1])

    iot_client.delete_thing(thingName=thing_name)
    print(f"deleted thing: {thing_name}")


def detach_thing_principal(principal: str, thing_name: str) -> None:
    policies = iot_client.list_attached_policies(target=principal)
    for policy in policies["policies"]:
        delete_iot_policy(policy["policyName"], principal)

    iot_client.detach_thing_principal(thingName=thing_name, principal=principal)


def delete_iot_policy(policy_name: str, principal: str) -> None:
    iot_client.detach_policy(policyName=policy_name, target=principal)
    iot_client.delete_policy(policyName=policy_name)
    print(f"deleted policy: {policy_name}")


if __name__ == "__main__":
    print("deleting simulated secrets...")
    for secret_arn in get_simulated_secrets():
        delete_secretsmanager_secret(secret_arn)

    print("deleting simulated things...")
    for iot_thing_name in get_simulated_things():
        delete_iot_thing(thing_name=iot_thing_name)
