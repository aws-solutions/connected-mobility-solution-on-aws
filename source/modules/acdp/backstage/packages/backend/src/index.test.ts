// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { PluginEnvironment } from "./types";

describe("test", () => {
  it("unbreaks the test runner", () => {
    const unbreaker = {} as PluginEnvironment;
    expect(unbreaker).toBeTruthy();
  });
});
