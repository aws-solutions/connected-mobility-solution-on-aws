// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { createPermission } from "@backstage/plugin-permission-common";

export const acdpBuildReadPermission = createPermission({
  name: "acdp.build.read",
  attributes: { action: "read" },
});

export const acdpBuildStartPermission = createPermission({
  name: "acdp.build.start",
  attributes: { action: undefined },
});

export const acdpMetricsReadPermission = createPermission({
  name: "acdp.metrics.read",
  attributes: { action: "read" },
});

export const acdpPartnerOfferingReadPermission = createPermission({
  name: "acdp.partner-offering.read",
  attributes: { action: "read" },
});

export const acdpPermissions = [
  acdpBuildReadPermission,
  acdpBuildStartPermission,
  acdpMetricsReadPermission,
  acdpPartnerOfferingReadPermission,
];
