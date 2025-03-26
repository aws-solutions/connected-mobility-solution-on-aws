// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { AcdpAccountDirectoryApi } from "..";
import { mockedAvailableAccounts, mockedAvailableRegions } from "../../mocks";
import { MockedAcdpAccountDirectoryService } from "../../service/mocks";

export class MockedAcdpAccountDirectoryApi extends AcdpAccountDirectoryApi {
  public constructor(
    acdpAccountDirectoryService: MockedAcdpAccountDirectoryService,
  ) {
    super(acdpAccountDirectoryService);
  }

  public getAvailableAccounts(): Promise<
    { awsAccountId: string; alias: string }[]
  > {
    return Promise.resolve(mockedAvailableAccounts);
  }

  public getAvailableRegions(): Promise<string[]> {
    return Promise.resolve(mockedAvailableRegions);
  }
}
