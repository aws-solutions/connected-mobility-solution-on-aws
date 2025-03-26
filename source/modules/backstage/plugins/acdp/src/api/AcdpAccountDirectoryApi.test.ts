// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { AcdpAccountDirectoryImpl } from ".";
import { mockGlobalFetch, mockAcdpBaseApiInput, baseUrl } from "../mocks";

const acdpAccountDirectoryApi = new AcdpAccountDirectoryImpl(
  mockAcdpBaseApiInput,
);

let mockedFetch: jest.SpyInstance;
beforeEach(() => {
  mockedFetch = mockGlobalFetch();
});

afterEach(() => {
  jest.clearAllMocks();
});

describe("AcdpAccountDirectoryApi", () => {
  it("should get available accounts", async () => {
    await acdpAccountDirectoryApi.getAvailableAccounts();

    const fetchCall = mockedFetch.mock.calls[0][0].valueOf() as Request;
    expect(fetchCall.method).toEqual("GET");
    expect(fetchCall.url).toEqual(
      `${baseUrl}/api/acdp/account-directory/available-accounts-for-all-orgs`,
    );
  });
  it("should get available regions", async () => {
    await acdpAccountDirectoryApi.getAvailableRegions();

    const fetchCall = mockedFetch.mock.calls[0][0].valueOf() as Request;
    expect(fetchCall.method).toEqual("GET");
    expect(fetchCall.url).toEqual(
      `${baseUrl}/api/acdp/account-directory/available-regions`,
    );
  });
});
