# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from abc import ABCMeta, abstractmethod
from functools import lru_cache
from typing import TYPE_CHECKING, Generator

# Third Party Libraries
import boto3

# Connected Mobility Solution on AWS
from ..source.config.constants import VPConstants

if TYPE_CHECKING:
    # Third Party Libraries
    from mypy_boto3_dynamodb.client import DynamoDBClient
    from mypy_boto3_iot.client import IoTClient

else:
    IoTClient = object
    DynamoDBClient = object


class ICleanup(metaclass=ABCMeta):
    @abstractmethod
    def cleanup(self) -> None:
        pass


class IotCoreCleanup(ICleanup):
    @lru_cache(128)
    def iot_client(self) -> IoTClient:
        return boto3.client("iot")

    def get_vehicle_things(self) -> Generator[str, None, None]:
        list_things_iterator = self.iot_client().get_paginator("list_things")

        for page in list_things_iterator.paginate():
            for thing in page["things"]:  # pylint: disable=W0621
                if thing["thingName"].startswith("Vehicle_"):
                    yield thing["thingName"]

    def delete_iot_thing(self, thing_name: str) -> None:
        principals = self.iot_client().list_thing_principals(thingName=thing_name)
        for principal in principals["principals"]:
            self.detach_thing_principal(principal=principal, thing_name=thing_name)
            if principal.split("/")[0].split(":")[-1] == "cert":
                certificate_id = principal.split("/")[-1]
                self.delete_certificate(certificate_id=certificate_id)

        self.iot_client().delete_thing(thingName=thing_name)
        print(f"Deleted iot thing: {thing_name}")

    def delete_certificate(self, certificate_id: str) -> None:
        self.iot_client().update_certificate(
            certificateId=certificate_id,
            newStatus="INACTIVE",
        )
        self.iot_client().delete_certificate(certificateId=certificate_id)
        print(f"Deleted iot certificate: {certificate_id}")

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
        print(f"Deleted iot policy: {policy_name}")

    def cleanup(self) -> None:
        for thing_name in self.get_vehicle_things():
            self.delete_iot_thing(thing_name=thing_name)

        print("\n***** Completed cleanup of IoT Core resources *****\n")


class DynamoDBCleanup(ICleanup):
    @lru_cache(128)
    def get_dynamodb_client(self) -> DynamoDBClient:
        return boto3.client("dynamodb")

    def get_ddb_tables(self) -> Generator[str, None, None]:
        all_ddb_table_names = self.get_dynamodb_client().list_tables()["TableNames"]
        tables_prefix = VPConstants.APP_NAME
        tables_to_delete = list(
            filter(
                lambda table_name: table_name.startswith(tables_prefix),
                all_ddb_table_names,
            )
        )
        for table in tables_to_delete:
            yield table

    def delete_ddb_table(self, table: str) -> None:
        self.get_dynamodb_client().delete_table(TableName=table)
        print(f"Deleted table: {table}")

    def cleanup(self) -> None:
        # delete ddb tables
        for table in self.get_ddb_tables():
            self.delete_ddb_table(table=table)

        print("\n***** Completed cleanup of DynamoDB resources *****\n")


if __name__ == "__main__":
    resource_cleanups = [
        DynamoDBCleanup,
        IotCoreCleanup,
    ]
    for resource_cleanup in resource_cleanups:
        resource_cleanup().cleanup()
