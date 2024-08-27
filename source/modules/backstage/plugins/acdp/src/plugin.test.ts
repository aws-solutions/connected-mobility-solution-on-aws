// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { acdpPlugin, EntityAcdpBuildProjectOverviewCard } from "./plugin";

describe("plugin", () => {
  it("should export acdp plugin", () => {
    expect(acdpPlugin).toBeDefined();
  });

  it("should export acdp CodeBuild Component", () => {
    expect(EntityAcdpBuildProjectOverviewCard).toBeDefined();
  });
});
