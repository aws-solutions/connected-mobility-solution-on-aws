# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import dataclasses


@dataclasses.dataclass(frozen=True)
class EmbeddingModelConfig:
    model_name: str


@dataclasses.dataclass(frozen=True)
class S3DataSourceConfig:
    bucket_name: str
    object_key_prefix: str
    bucket_owner_account_id: str


@dataclasses.dataclass(frozen=True)
class DataSourceChunkingConfig:
    strategy: str
    max_tokens: int
    overlap_percentage: int


@dataclasses.dataclass(frozen=True)
class VectorMethod:
    name: str
    space_type: str
    engine: str
    ef_construction: int
    m: int


@dataclasses.dataclass(frozen=True)
class VectorConfig:
    name: str
    metadata_field: str
    text_field: str
    vector_type: str
    dimension: str
    method: VectorMethod


@dataclasses.dataclass(frozen=True)
class VectorIndexConfig:
    name: str
    vector: VectorConfig


@dataclasses.dataclass(frozen=True)
class AgentConfig:
    instruction: str
    foundational_model_id: str
    idle_session_ttl_in_seconds: int


@dataclasses.dataclass(frozen=True)
class ChatbotConstructOutputs:
    knowledge_base_id: str
    agent_id: str
    agent_alias_id: str
