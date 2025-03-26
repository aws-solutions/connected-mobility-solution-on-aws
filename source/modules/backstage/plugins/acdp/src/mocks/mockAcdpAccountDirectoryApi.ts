// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { AvailableAccountsProps } from "backstage-plugin-acdp-common";

export const mockedAvailableAccounts = [
  { awsAccountId: "123456789012", alias: "Account1" },
  { awsAccountId: "987654321098", alias: "Account2" },
  { awsAccountId: "112233445566", alias: "Account3" },
];

export const mockedAvailableRegions = [
  "us-east-1",
  "us-west-2",
  "eu-central-1",
];

export class MockAcdpAccountDirectoryApi {
  async getAvailableAccounts(): Promise<AvailableAccountsProps[]> {
    return mockedAvailableAccounts;
  }
  async getAvailableRegions(): Promise<string[]> {
    return mockedAvailableRegions;
  }
}
