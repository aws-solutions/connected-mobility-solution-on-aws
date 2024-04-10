# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import os
import random
import time

# AWS Libraries
import boto3

AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_SESSION_TOKEN = os.environ.get("AWS_SESSION_TOKEN")
STAGE = os.environ.get("STAGE", "dev")
PROFILE = None

if not all([AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN]):
    PROFILE = os.environ.get(
        "AWS_PROFILE",
        input(f"Which AWS profile {boto3.session.Session().available_profiles}: "),
    )

session = boto3.Session(profile_name=PROFILE)
resourcetagging_api_client = session.client("resourcegroupstaggingapi")
sns_client = session.client("sns")
ssm_client = session.client("ssm")

deployement_uuid = ssm_client.get_parameter(
    Name=f"/{STAGE}/cms/common/config/deployment-uuid"
)["Parameter"]["Value"]

pagination_config = {
    "MaxResults": 150,  # rate limit of 150 transactions per second
    "PaginationToken": "",
}

# Initialize variables for exponential backoff
MAX_RETRIES = 5
BASE_DELAY = 0.2
MAX_DELAY = 5.0

while True:
    response = resourcetagging_api_client.get_resources(
        ResourceTypeFilters=["sns:topic"],
        TagFilters=[{"Key": "AlertsUUID", "Values": [deployement_uuid]}],
        PaginationToken=pagination_config["PaginationToken"],
    )

    for resource in response.get("ResourceTagMappingList", []):
        topic_arn = resource["ResourceARN"]
        print(f"Deleting Topic with ARN: {topic_arn}")

        RETRIES = 0
        while RETRIES <= MAX_RETRIES:
            try:
                sns_client.delete_topic(TopicArn=topic_arn)
                break
            except Exception as e:  # pylint: disable=broad-exception-caught
                print(f"An error occurred: {e}")
                RETRIES += 1
                if RETRIES > MAX_RETRIES:
                    print(f"Max RETRIES reached for Topic ARN: {topic_arn}")

                # exponential backoff with jitter
                delay = min(MAX_DELAY, (2**RETRIES) * BASE_DELAY)
                time.sleep(
                    delay
                    + random.uniform(  # nosec :not used for security purposes
                        0, 0.1 * (2**RETRIES)
                    )
                )

    # Check for more pages
    if "PaginationToken" in response and response["PaginationToken"]:
        pagination_config["PaginationToken"] = response["PaginationToken"]
    else:
        break
