// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

// SPDX-License-Identifier: Apache-2.0

import { acdpPlugin } from "./plugin";

describe("plugin", () => {
  it("should export acdp plugin", () => {
    expect(acdpPlugin).toBeDefined();
  });
});
