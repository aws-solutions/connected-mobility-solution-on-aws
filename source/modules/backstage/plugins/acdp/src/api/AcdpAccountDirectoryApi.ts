// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { createApiRef } from "@backstage/frontend-plugin-api";

import { AcdpBaseApi, AcdpBaseApiInput } from "./AcdpBaseApi";

import { AvailableAccountsProps } from "backstage-plugin-acdp-common";

export interface AcdpAccountDirectoryApi extends AcdpBaseApi {
  getAvailableAccounts(): Promise<AvailableAccountsProps[]>;
  getAvailableRegions(): Promise<string[]>;
}
export class AcdpAccountDirectoryImpl extends AcdpBaseApi {
  public constructor(options: AcdpBaseApiInput) {
    super(options);
  }

  async getAvailableAccounts(): Promise<AvailableAccountsProps[]> {
    const urlSegment = `/account-directory/available-accounts-for-all-orgs`;

    return await this._fetch<AvailableAccountsProps[]>(urlSegment);
  }

  async getAvailableRegions(): Promise<string[]> {
    const urlSegment = `/account-directory/available-regions`;

    return await this._fetch<string[]>(urlSegment);
  }
}

export const acdpAccountDirectoryApiRef = createApiRef<AcdpAccountDirectoryApi>(
  {
    id: "plugin.acdpaccountdirectory.service",
  },
);
