// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { CatalogClient } from "@backstage/catalog-client";
import { Entity } from "@backstage/catalog-model";
import { AcdpApplication } from "backstage-plugin-acdp-common";

import { AcdpMetricsService } from "../service";
import { AcdpBaseApi } from "./acdp-base-api";

export class AcdpMetricsApi extends AcdpBaseApi {
  private acdpMetricsService: AcdpMetricsService;

  public constructor(
    catalogClient: CatalogClient,
    acdpMetricsService: AcdpMetricsService,
  ) {
    super(catalogClient, acdpMetricsService._logger);
    this.acdpMetricsService = acdpMetricsService;
  }

  public async getApplicationByEntity(
    entity: Entity,
  ): Promise<AcdpApplication | undefined> {
    const appRegistryApplication =
      await this.acdpMetricsService.getApplicationByEntity(entity);

    return appRegistryApplication
      ? {
          arn: appRegistryApplication.arn,
          applicationTag: appRegistryApplication.applicationTag,
        }
      : undefined;
  }

  public async getApplicationByArn(
    arn: string,
  ): Promise<AcdpApplication | undefined> {
    const appRegistryApplication =
      await this.acdpMetricsService.getApplicationByArn(arn);

    return appRegistryApplication
      ? {
          arn: appRegistryApplication.arn,
          applicationTag: appRegistryApplication.applicationTag,
        }
      : undefined;
  }

  public async getNetUnblendedCurrentMonthCost(
    entity: Entity,
    awsApplicationTag: string,
  ): Promise<string> {
    return await this.acdpMetricsService.getNetUnblendedCurrentMonthCost(
      entity,
      awsApplicationTag,
    );
  }
}
