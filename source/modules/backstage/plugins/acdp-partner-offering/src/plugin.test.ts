// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { acdpPartnerOfferingPlugin } from "./plugin";

describe("acdp-partner-offering", () => {
  it("should export plugin", () => {
    expect(acdpPartnerOfferingPlugin).toBeDefined();
  });
});
