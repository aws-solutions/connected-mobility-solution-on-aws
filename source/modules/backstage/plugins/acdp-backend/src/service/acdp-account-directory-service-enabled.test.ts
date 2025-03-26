// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { mockClient } from "aws-sdk-client-mock";
import {
  OrganizationsClient,
  ListAccountsForParentCommand,
} from "@aws-sdk/client-organizations";
import { SSMClient, GetParameterCommand } from "@aws-sdk/client-ssm";
import { mockServices } from "@backstage/backend-test-utils";
import {
  AcdpAccountDirectoryService,
  AcdpAccountDirectoryServiceOptions,
} from "./acdp-account-directory-service";
import { mockCredentialsProvider, mockConfigWithMultiAccount } from "../mocks";

const mockedOrganizationsClient = mockClient(OrganizationsClient);
const mockedSSMClient = mockClient(SSMClient);

let acdpAccountDirectoryService: AcdpAccountDirectoryService;

beforeAll(async () => {
  const options: AcdpAccountDirectoryServiceOptions = {
    config: mockConfigWithMultiAccount,
    awsCredentialsProvider: mockCredentialsProvider,
    logger: mockServices.logger.mock(),
  };
  acdpAccountDirectoryService = new AcdpAccountDirectoryService(options);
});

beforeEach(() => {
  mockedOrganizationsClient.reset();
  mockedSSMClient.reset();
});

describe("AcdpAccountDirectoryService", () => {
  describe("getAvailableAccounts", () => {
    it("should return available accounts from organizations when multi-account deployment is enabled", async () => {
      mockedSSMClient
        .on(GetParameterCommand, {
          Name: acdpAccountDirectoryService.enrolledOrgsParameterName,
        })
        .resolves({ Parameter: { Value: "ou-123" } });

      mockedOrganizationsClient.on(ListAccountsForParentCommand).resolves({
        Accounts: [
          { Id: "123456789012", Name: "Account1" },
          { Id: "987654321098", Name: "Account2" },
        ],
      });

      const accounts = await acdpAccountDirectoryService.getAvailableAccounts();

      expect(accounts).toEqual([
        { awsAccountId: "123456789012", alias: "Account1" },
        { awsAccountId: "987654321098", alias: "Account2" },
      ]);
    });
  });

  describe("getAvailableRegions", () => {
    it("should return available regions from SSM when multi-account deployment is enabled", async () => {
      mockedSSMClient
        .on(GetParameterCommand)
        .resolves({ Parameter: { Value: "us-east-1,us-west-2" } });

      const regions = await acdpAccountDirectoryService.getAvailableRegions();
      expect(regions).toEqual(["us-east-1", "us-west-2"]);
    });
  });
});
