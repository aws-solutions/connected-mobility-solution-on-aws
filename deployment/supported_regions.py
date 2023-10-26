# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import functools
import json
from typing import Any, Dict

# Third Party Libraries
import requests

LIST_OF_USED_SERVICES = [
    "Amazon Managed Grafana",
    "Amazon API Gateway",
    "Elastic Load Balancing",
    "Amazon Aurora",
    "AWS Certificate Manager",
    "AWS CodeBuild",
    "AWS CodePipeline",
    "AWS CodeStar",
    "Amazon Cognito",
    "AWS CloudFormation",
    "Amazon CloudFront",
    "Amazon CloudWatch",
    "Amazon Elastic Container Service (ECS)",
    "Amazon Elastic Container Registry (ECR)",
    "Amazon Elastic Compute Cloud (EC2)",
    "Amazon DynamoDB",
    "AWS Fargate",
    "AWS Glue",
    "AWS Identity and Access Management (IAM)",
    "AWS IoT Core",
    "AWS Key Management Service",
    "Amazon Kinesis Data Firehose",
    "AWS Lambda",
    "Amazon Location Service",
    "AWS Proton",
    "Amazon Route 53",
    "AWS Secrets Manager",
    "Amazon Simple Storage Service (S3)",
    "AWS Step Functions",
    "AWS Systems Manager",
    "Amazon Virtual Private Cloud (VPC)",
    "AWS X-Ray",
]

ALL_REGIONS = {
    "ap-northeast-2",
    "eu-west-2",
    "eu-central-2",
    "us-west-1",
    "eu-south-1",
    "eu-south-2",
    "ap-northeast-1",
    "ap-east-1",
    "us-gov-east-1",
    "ca-central-1",
    "ap-southeast-1",
    "ap-northeast-3",
    "ap-southeast-3",
    "us-east-1",
    "eu-north-1",
    "ap-south-2",
    "ap-southeast-2",
    "cn-north-1",
    "eu-west-3",
    "sa-east-1",
    "us-gov-west-1",
    "ap-southeast-4",
    "us-east-2",
    "us-west-2",
    "eu-central-1",
    "ap-south-1",
    "cn-northwest-1",
    "af-south-1",
    "me-south-1",
    "me-central-1",
    "eu-west-1",
}


def load_region_data() -> Dict[str, Any]:
    data = requests.get(
        "https://api.regional-table.region-services.aws.a2z.com/index.json", timeout=10
    )
    region_dict: Dict[str, Any] = json.loads(data.content)

    return region_dict


def check_expected_service_names(region_data: Dict[str, Any]) -> None:
    unique_set = set()

    for region_service in region_data["prices"]:
        # print(region_service["attributes"]["aws:serviceName"])
        unique_set.add(region_service["attributes"]["aws:serviceName"])
        ALL_REGIONS.add(region_service["attributes"]["aws:region"])

    missing_names = [item for item in LIST_OF_USED_SERVICES if item not in unique_set]

    if missing_names:
        print(json.dumps(list(unique_set), indent=2))
        print("------------")
        print("expected services not found:\n")
        print(json.dumps(missing_names, indent=2))


def region_cross_reference(region_data: Dict[str, Any]) -> set[str]:
    def service_regions(service_name: str) -> set[str]:
        regions = set()
        for data in region_data["prices"]:
            if data["attributes"]["aws:serviceName"] == service_name:
                regions.add(data["attributes"]["aws:region"])

        print("-", service_name, "-", len(regions), "-\n-", regions, "\n")

        if len(regions) < service_regions.most_limited_service[1]:  # type: ignore
            service_regions.most_limited_service = (service_name, len(regions))  # type: ignore

        return regions

    service_regions.most_limited_service = ("N/A", 999)  # type: ignore
    possible_regions = functools.reduce(
        lambda x, y: x.intersection(service_regions(y)),
        LIST_OF_USED_SERVICES,
        ALL_REGIONS,
    )

    print("-----------")
    print(sorted(list(possible_regions)))
    print(service_regions.most_limited_service)  # type: ignore
    return possible_regions


if __name__ == "__main__":
    aws_region_service_data = load_region_data()

    check_expected_service_names(region_data=aws_region_service_data)

    region_cross_reference(region_data=aws_region_service_data)

    # Go here to view region display names:
    # - https://w.amazon.com/bin/view/AWSDocs/new-service/update-general-reference/#HRegionairportcodes
