// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { Entity } from "@backstage/catalog-model";

import { constants } from "backstage-plugin-acdp-common";

export const isApplicationArnAvailable = (entity: Entity) => {
  return Boolean(
    entity.metadata.annotations?.[
      constants.APP_REGISTRY_APPLICATION_ARN_ANNOTATION
    ],
  );
};

export const isDeploymentTargetAvailable = (entity: Entity) => {
  return Boolean(
    entity.metadata.annotations?.[constants.ACDP_DEPLOYMENT_TARGET_ANNOTATION],
  );
};
