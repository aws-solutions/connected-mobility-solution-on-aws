// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { partnerOfferingEntityModel } from "./module";

describe("module", () => {
  it("should export acdp partner offering module", () => {
    expect(partnerOfferingEntityModel).toBeDefined();
  });
});
