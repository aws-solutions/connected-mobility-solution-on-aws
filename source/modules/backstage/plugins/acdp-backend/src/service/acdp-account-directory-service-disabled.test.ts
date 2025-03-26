// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { mockServices } from "@backstage/backend-test-utils";
import {
  AcdpAccountDirectoryService,
  AcdpAccountDirectoryServiceOptions,
} from "./acdp-account-directory-service";
import {
  mockCredentialsProvider,
  mockConfigWithoutMultiAccount,
} from "../mocks";

let acdpAccountDirectoryService: AcdpAccountDirectoryService;

beforeAll(async () => {
  const options: AcdpAccountDirectoryServiceOptions = {
    config: mockConfigWithoutMultiAccount,
    awsCredentialsProvider: mockCredentialsProvider,
    logger: mockServices.logger.mock(),
  };
  acdpAccountDirectoryService = new AcdpAccountDirectoryService(options);
});

describe("AcdpAccountDirectoryService", () => {
  describe("getAvailableAccounts", () => {
    it("should return default account when multi-account deployment is disabled", async () => {
      const accounts = await acdpAccountDirectoryService.getAvailableAccounts();
      expect(accounts).toEqual([
        {
          awsAccountId:
            acdpAccountDirectoryService._defaultDeploymentTarget.awsAccountId,
          alias: "DEFAULT",
        },
      ]);
    });
  });

  describe("getAvailableRegions", () => {
    it("should return default region when multi-account deployment is disabled", async () => {
      acdpAccountDirectoryService.enableMultiAccountDeployment = false;
      const regions = await acdpAccountDirectoryService.getAvailableRegions();
      expect(regions).toEqual([
        acdpAccountDirectoryService._defaultDeploymentTarget.awsRegion,
      ]);
    });
  });
});
