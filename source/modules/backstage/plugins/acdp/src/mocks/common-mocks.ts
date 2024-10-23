// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { MockConfigApi } from "@backstage/test-utils";

import { AcdpBaseApiInput } from "../api";

export const baseUrl: string = "https://example.com";

export const mockGlobalFetch = (): jest.SpyInstance => {
  return jest.spyOn(global, "fetch").mockImplementation((input) => {
    const { status, ok } = (input.valueOf() as Request).url.includes(
      "arn=bad-arn",
    )
      ? { status: 404, ok: false }
      : { status: 200, ok: true };
    return Promise.resolve({
      text: () => Promise.resolve(""),
      status,
      ok,
    } as Response);
  });
};

export const mockAcdpBaseApiInput: AcdpBaseApiInput = {
  configApi: new MockConfigApi({
    backend: {
      baseUrl,
    },
  }),
  identityApi: {
    getBackstageIdentity: jest.fn(),
    getCredentials: jest.fn().mockReturnValue({ token: "test" }),
    getProfileInfo: jest.fn(),
    signOut: jest.fn(),
  },
};
