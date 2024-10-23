// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { CatalogClient } from "@backstage/catalog-client";

import { AcdpApplication } from "backstage-plugin-acdp-common";

import { AcdpMetricsApi } from "..";
import {
  mockedApplicationArn,
  mockedApplicationTag,
  mockedCurrentMonthCost,
} from "../../mocks";
import { MockedAcdpMetricsService } from "../../service/mocks";

export class MockedAcdpMetricsApi extends AcdpMetricsApi {
  mockedApplication: AcdpApplication;

  public constructor(
    catalogClient: CatalogClient,
    acdpMetricsService: MockedAcdpMetricsService,
  ) {
    super(catalogClient, acdpMetricsService);
    this.mockedApplication = {
      arn: mockedApplicationArn,
      applicationTag: {
        awsApplication: mockedApplicationTag,
      },
    };
  }

  public getApplicationByEntity(): Promise<AcdpApplication> {
    return Promise.resolve(this.mockedApplication);
  }

  public getApplicationByArn(): Promise<AcdpApplication> {
    return Promise.resolve(this.mockedApplication);
  }

  public getNetUnblendedCurrentMonthCost(): Promise<string> {
    return Promise.resolve(mockedCurrentMonthCost);
  }
}
