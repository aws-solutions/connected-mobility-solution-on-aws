# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import argparse
from pprint import pprint

# AWS Libraries
import boto3

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", type=str)
    parser.add_argument(
        "--app-unique-id",
        action="store",
        type=str,
        default="cms",
    )
    args = parser.parse_args()

    ssm_client = boto3.client("ssm")
    bedrock_agents_runtime_client = boto3.client("bedrock-agent-runtime")

    MODEL_ID = "anthropic.claude-v2"
    model_arn = f"arn:aws:bedrock:us-east-1::foundation-model/{MODEL_ID}"

    knowledge_base_id = ssm_client.get_parameter(
        Name=f"/solution/{args.app_unique_id}/predictive-maintenance/chatbot/knowledge-base-id"
    )["Parameter"]["Value"]

    response = bedrock_agents_runtime_client.retrieve_and_generate(
        input={"text": args.query},
        retrieveAndGenerateConfiguration={
            "type": "KNOWLEDGE_BASE",
            "knowledgeBaseConfiguration": {
                "knowledgeBaseId": knowledge_base_id,
                "modelArn": model_arn,
            },
        },
    )

    pprint(response["output"]["text"])
