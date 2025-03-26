// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { techdocsModuleCustomBuildStrategy } from "./module";

describe("module", () => {
  it("should export techdocs custom build strategy module", () => {
    expect(techdocsModuleCustomBuildStrategy).toBeDefined();
  });
});
