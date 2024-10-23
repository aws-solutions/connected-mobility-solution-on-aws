# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import argparse

# Third Party Libraries
import requests

# AWS Libraries
import boto3

# CMS Common Library
from cms_common.auth.auth_configs import get_idp_config, get_service_client_config
from cms_common.resource_names.config import ConfigResourceNames


def get_access_token(identity_provider_id: str, user_agent_string: str = "") -> str:
    idp_config = get_idp_config(
        user_agent_string=user_agent_string,
        identity_provider_id=identity_provider_id,
    )
    client_config = get_service_client_config(
        user_agent_string=user_agent_string,
        identity_provider_id=identity_provider_id,
    )

    client_credentials_payload = {
        "grant_type": "client_credentials",
        "audience": client_config.audience,
        "client_id": client_config.client_id,
        "client_secret": client_config.client_secret,
    }

    client_credentials_flow_response = requests.post(
        url=idp_config.token_endpoint,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data=client_credentials_payload,
        timeout=10,
    )

    assert client_credentials_flow_response.ok

    return str(client_credentials_flow_response.json()["access_token"])


def main(args: argparse.Namespace) -> None:
    ssm_client = boto3.client("ssm")
    config_resource_names = ConfigResourceNames.from_app_unique_id(args.app_unique_id)
    identity_provider_id = config_resource_names.identity_provider_id_ssm_parameter
    predict_api_url = ssm_client.get_parameter(
        Name=f"/solution/{args.app_unique_id}/predictive-maintenance/api/predict/endpoint/url"
    )["Parameter"]["Value"]

    access_token = get_access_token(identity_provider_id=identity_provider_id)

    api_headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"{access_token}",
    }

    response = requests.post(
        url=predict_api_url,
        json={"input": args.model_input},
        headers=api_headers,
        timeout=30,
    )
    print(f"Response Status Code: {response.status_code}")
    print(f"Response Body: {response.json()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--app-unique-id", type=str, default="cms")
    parser.add_argument("--model-input", type=str)
    parsed_args = parser.parse_args()

    main(args=parsed_args)
