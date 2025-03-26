// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { AcdpAccountDirectoryApi } from "../api/acdp-account-directory-api";
import { MockedAcdpAccountDirectoryService } from "../service/mocks";
import { mockedAvailableAccounts, mockedAvailableRegions } from "../mocks";
import { mockClient } from "aws-sdk-client-mock";
import {
  ListAccountsForParentCommand,
  OrganizationsClient,
} from "@aws-sdk/client-organizations";
import { GetParameterCommand, SSMClient } from "@aws-sdk/client-ssm";

const mockedOrganizationsClient = mockClient(OrganizationsClient);
const mockedSSMClient = mockClient(SSMClient);

let mockedAcdpAccountDirectoryService: MockedAcdpAccountDirectoryService;
let acdpAccountDirectoryApi: AcdpAccountDirectoryApi;

beforeAll(async () => {
  mockedAcdpAccountDirectoryService = new MockedAcdpAccountDirectoryService();
  acdpAccountDirectoryApi = new AcdpAccountDirectoryApi(
    mockedAcdpAccountDirectoryService,
  );
});

beforeEach(() => {
  mockedOrganizationsClient.reset();
  mockedSSMClient.reset();
});

describe("AcdpAccountDirectoryApi", () => {
  describe("getAvailableAccounts", () => {
    it("should return the list of available accounts", async () => {
      mockedSSMClient
        .on(GetParameterCommand, {
          Name: mockedAcdpAccountDirectoryService.enrolledOrgsParameterName,
        })
        .resolves({ Parameter: { Value: "ou-123" } });

      mockedOrganizationsClient.on(ListAccountsForParentCommand).resolves({
        Accounts: mockedAvailableAccounts.map((account) => {
          return { Id: account.awsAccountId, Name: account.alias };
        }),
      });
      const accounts = await acdpAccountDirectoryApi.getAvailableAccounts();
      expect(accounts).toEqual(mockedAvailableAccounts);
    });
  });

  describe("getAvailableRegions", () => {
    it("should return the list of available regions", async () => {
      mockedSSMClient
        .on(GetParameterCommand)
        .resolves({ Parameter: { Value: mockedAvailableRegions.join(",") } });

      const regions = await acdpAccountDirectoryApi.getAvailableRegions();
      expect(regions).toEqual(mockedAvailableRegions);
    });
  });
});
