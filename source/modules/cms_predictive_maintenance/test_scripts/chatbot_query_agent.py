# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import argparse
import uuid
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

    agent_id = ssm_client.get_parameter(
        Name=f"/solution/{args.app_unique_id}/predictive-maintenance/chatbot/agent-id"
    )["Parameter"]["Value"]

    response = bedrock_agents_runtime_client.invoke_agent(
        agentAliasId="TSTALIASID",
        agentId=agent_id,
        enableTrace=True,
        endSession=False,
        inputText=args.query,
        sessionId=str(uuid.uuid4()),
    )

    completion: str = ""
    for event in response.get("completion"):
        chunk = event.get("chunk", {"bytes": b""})
        completion += chunk["bytes"].decode()
    pprint(completion)
