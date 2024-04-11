# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0


# Standard Library
import argparse
import json
import os
import re
from dataclasses import dataclass

# AWS Libraries
import boto3


@dataclass
class Outputs:
    cognito_client_id: str = "consoleclientid"
    console_url: str = "consoleurl"
    region: str = "region"
    rest_api_id: str = "restapiid"
    stage_name: str = "apigatewaystage"
    user_email: str = "adminuseremail"

    cfn_outputs = {}  # type: ignore
    generic = False

    def get_output(self, field: str) -> str:
        if not (found := self.cfn_outputs.get(field, "")):
            print(f"Unable to find expected output: {field}")

        if self.generic and field not in [self.rest_api_id, self.stage_name]:
            found = "a_value"

        return str(found)

    def get_cfn_outputs(self, stack_name: str, region_name: str) -> None:
        cf_client = boto3.client(
            "cloudformation",
            region_name=region_name,
        )

        (stack,) = cf_client.describe_stacks(StackName=stack_name)["Stacks"]
        stack_outputs = stack["Outputs"]

        output_result = {}

        for output in stack_outputs:
            key = output["OutputKey"]
            output_result[key] = output["OutputValue"]

        if not output_result.get(Outputs.region):
            output_result[Outputs.region] = region_name

        self.cfn_outputs = output_result

    def get_api_export(self, region_name: str) -> str:
        response = boto3.client("apigateway", region_name=region_name).get_export(
            restApiId=self.get_output(self.rest_api_id),
            stageName=self.get_output(self.stage_name),
            exportType="oas30",
            parameters={"extensions": "postman"},
            accepts="application/json",
        )
        response_body: str = response["body"].read().decode("utf-8")

        if self.generic:
            response_body = re.sub(
                "https.*amazonaws.com", "https://domain.amazonaws.com", response_body
            )

        return response_body


def generate_postman_env(data_class: Outputs, stack_name: str) -> str:
    # Remove trailing slash for cleanliness in postman
    api_base_url = data_class.get_output(data_class.console_url).strip("/")
    api_region = data_class.get_output(data_class.region)
    cognito_client_id = data_class.get_output(data_class.cognito_client_id)
    cognito_user_name = data_class.get_output(data_class.user_email)

    env = {
        "id": f"{stack_name}-env",
        "name": f"{stack_name} Environment",
        "values": [
            {
                "key": "API_BASE_URL",
                "value": api_base_url,
                "type": "default",
                "enabled": True,
            },
            {"key": "region", "value": api_region, "type": "default", "enabled": True},
            {
                "key": "cognitoClientId",
                "value": cognito_client_id,
                "type": "default",
                "enabled": True,
            },
            {
                "key": "cognitoUserName",
                "value": cognito_user_name,
                "type": "default",
                "enabled": True,
            },
            {
                "key": "cognitoUserPassword",
                "value": "",
                "type": "secret",
                "enabled": True,
            },
            {
                "key": "cognitoAccessToken",
                "value": "",
                "type": "default",
                "enabled": True,
            },
            {"key": "cognitoIdToken", "value": "", "type": "default", "enabled": True},
            {"key": "token_expiration", "value": "", "type": "any", "enabled": True},
        ],
        "_postman_variable_scope": "environment",
    }

    return json.dumps(env, indent=4)


def write_files(args: argparse.Namespace) -> None:
    # If the output field values differ from above, instantiate the class with the overrides and the rest will work
    data = Outputs()
    data.generic = args.commit
    data.get_cfn_outputs(stack_name=args.stack_name, region_name=args.region)

    postman_env = generate_postman_env(data, args.stack_name)

    with open(
        f"./documentation/postman/postman-{args.stack_name}.env.json",
        "w",
        encoding="utf-8",
    ) as outfile:
        outfile.write(postman_env)

        print(f"Wrote postman env file to {os.path.abspath(outfile.name)}")

    postman_collection = data.get_api_export(region_name=args.region)

    with open(
        f"./documentation/postman/postman-{args.stack_name}.json", "w", encoding="utf-8"
    ) as outfile:
        outfile.write(postman_collection)

        print(f"Wrote postman collection file to {os.path.abspath(outfile.name)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="cms-vehicle-simulator",
        description="A script to generate postman (Open API) files to be imported.",
    )

    parser.add_argument(
        "--stack-name",
        action="store",
        type=str,
        default="cms-vehicle-simulator-stack-dev",
        help="The name of the CloudFormation stack.",
    )
    parser.add_argument(
        "--region",
        "-e",
        action="store",
        choices=["us-east-1", "us-east-2", "us-west-2", "eu-west-1"],
        default="us-east-1",
        help="Specify the region where the stack is deployed.",
    )
    parser.add_argument(
        "--profile",
        action="store",
        type=str,
        default=None,
        help="The AWS Config profile to use.",
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        default=False,
        help="Write postman files generically so they can be committed to the repo.",
    )

    write_files(parser.parse_args())
