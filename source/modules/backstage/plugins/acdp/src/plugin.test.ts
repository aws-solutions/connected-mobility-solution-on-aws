// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {
  acdpPlugin,
  EntityAcdpBuildProjectOverviewCard,
  EntityApplicationsDashboardLinkCard,
} from "./plugin";

describe("plugin", () => {
  it("should export acdp plugin", () => {
    expect(acdpPlugin).toBeDefined();
  });

  it("should export CodeBuild Project Overview Card", () => {
    expect(EntityAcdpBuildProjectOverviewCard).toBeDefined();
  });

  it("should export Applications Dashboard Link card", () => {
    expect(EntityApplicationsDashboardLinkCard).toBeDefined();
  });
});
