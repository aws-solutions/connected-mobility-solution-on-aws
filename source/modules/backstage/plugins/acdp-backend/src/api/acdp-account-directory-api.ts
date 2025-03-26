// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0
import { AcdpAccountDirectoryService } from "../service/acdp-account-directory-service";
import { LoggerService } from "@backstage/backend-plugin-api/index";
import { AvailableAccountsProps } from "backstage-plugin-acdp-common";

export class AcdpAccountDirectoryApi {
  private acdpAccountDirectoryService: AcdpAccountDirectoryService;
  _logger: LoggerService;

  public constructor(acdpAccountDirectoryService: AcdpAccountDirectoryService) {
    this._logger = acdpAccountDirectoryService._logger;
    this.acdpAccountDirectoryService = acdpAccountDirectoryService;
  }

  public async getAvailableAccounts(): Promise<AvailableAccountsProps[]> {
    return await this.acdpAccountDirectoryService.getAvailableAccounts();
  }

  public async getAvailableRegions(): Promise<string[]> {
    return await this.acdpAccountDirectoryService.getAvailableRegions();
  }
}
