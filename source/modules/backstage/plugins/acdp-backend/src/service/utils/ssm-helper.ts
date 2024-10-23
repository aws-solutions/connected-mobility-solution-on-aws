// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import * as path from "path";

import { Entity, getCompoundEntityRef } from "@backstage/catalog-model";

import { constants } from "backstage-plugin-acdp-common";

export function getSsmParameterNameForEntityBuildParameters(
  prefix: string,
  entity: Entity,
) {
  const { kind, namespace, name } = getCompoundEntityRef(entity);
  return path.posix.join(
    prefix,
    kind.toLowerCase(),
    namespace.toLowerCase(),
    name.toLowerCase(),
    constants.BUILD_PARAMETER_SSM_POSTFIX,
  );
}

export function getSsmParameterNameForEntitySourceConfig(
  prefix: string,
  entity: Entity,
) {
  const { kind, namespace, name } = getCompoundEntityRef(entity);
  return path.posix.join(
    prefix,
    kind.toLowerCase(),
    namespace.toLowerCase(),
    name.toLowerCase(),
    constants.BUILD_SOURCE_CONFIG_SSM_POSTFIX,
  );
}
