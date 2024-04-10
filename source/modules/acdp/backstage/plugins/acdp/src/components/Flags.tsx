// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { Entity } from "@backstage/catalog-model";
import { constants } from "backstage-plugin-acdp-common";

export const isAcdpBuildProjectAvailable = (entity: Entity) => {
  return Boolean(
    entity.metadata.annotations?.[constants.ACDP_DEPLOYMENT_TARGET_ANNOTATION],
  );
};
