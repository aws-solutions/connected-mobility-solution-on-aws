// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { Entity } from "@backstage/catalog-model";

import { constants } from "backstage-plugin-acdp-common";

export function hasDocs(): (entity: Entity) => boolean {
  return (entity: Entity) => {
    return Boolean(
      entity.metadata.annotations?.[constants.BACKSTAGE_TECHDOCS_ANNOTATION],
    );
  };
}

export function hasCicd(): (entity: Entity) => boolean {
  return (entity: Entity) => {
    return Boolean(
      entity.metadata.annotations?.[
        constants.ACDP_DEPLOYMENT_TARGET_ANNOTATION
      ],
    );
  };
}

export function hasApis(): (entity: Entity) => boolean {
  return (entity: Entity) => {
    return (
      Boolean(entity.spec?.providesApis) || Boolean(entity.spec?.consumesApis)
    );
  };
}

export function hasDependencies(): (entity: Entity) => boolean {
  return (entity: Entity) => {
    return Boolean(entity.spec?.dependsOn);
  };
}
