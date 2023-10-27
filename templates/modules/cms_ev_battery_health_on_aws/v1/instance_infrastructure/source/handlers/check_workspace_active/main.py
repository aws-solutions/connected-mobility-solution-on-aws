# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import os
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Dict

# Third Party Libraries
import boto3
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.config import Config

if TYPE_CHECKING:
    # Third Party Libraries
    from mypy_boto3_grafana.client import ManagedGrafanaClient
else:
    ManagedGrafanaClient = object

tracer = Tracer()
logger = Logger()


@lru_cache(maxsize=128)
def get_grafana_client() -> ManagedGrafanaClient:
    return boto3.client(
        "grafana", config=Config(user_agent_extra=os.environ["USER_AGENT_STRING"])
    )


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    workspace_active = False
    try:
        grafana_workspace_id = os.environ["GRAFANA_WORKSPACE_ID"]
        workspace = get_grafana_client().describe_workspace(
            workspaceId=grafana_workspace_id,
        )
        workspace_active = workspace["workspace"]["status"] == "ACTIVE"
        logger.info(f"Workspace active?: {workspace_active}")
    except KeyError:
        logger.error(
            "Key error when determining if workspace is active!", exc_info=True
        )
    except get_grafana_client().exceptions.ResourceNotFoundException:
        logger.error("Grafana workspace not found!", exc_info=True)

    return {"IsComplete": workspace_active}
