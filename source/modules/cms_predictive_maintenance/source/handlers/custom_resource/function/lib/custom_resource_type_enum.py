# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from enum import Enum


class CustomResourceFunctionType(Enum):
    GET_AOSS_VPC_ENDPOINT_ID = "GetAOSSVPCEndpointId"
    MANAGE_AOSS_VECTOR_INDEX = "ManageAOSSVectorIndex"
    INGEST_BEDROCK_DATA_SOURCE = "IngestBedrockDataSource"

    CREATE_AND_UPLOAD_SAGEMAKER_PIPELINE_DEFINITION = (
        "CreateAndUploadSageMakerPipelineDefinition"
    )
    DELETE_SAGEMAKER_DOMAIN_EFS = "DeleteSageMakerDomainEfs"
