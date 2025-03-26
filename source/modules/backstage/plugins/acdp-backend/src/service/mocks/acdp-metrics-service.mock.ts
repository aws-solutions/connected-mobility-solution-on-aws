// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { Application } from "@aws-sdk/client-service-catalog-appregistry";

import { LoggerService } from "@backstage/backend-plugin-api";
import { mockServices } from "@backstage/backend-test-utils";
import { Entity } from "@backstage/catalog-model";
import { Config } from "@backstage/config";
import { AwsCredentialProvider } from "@backstage/integration-aws-node";

import { constants } from "backstage-plugin-acdp-common";

import {
  mockedApplicationArn,
  mockedApplicationTag,
  mockedCurrentMonthCost,
  mockCredentialsProvider,
  mockedCatalogEntity,
  mockConfigWithoutMultiAccount,
} from "../../mocks";
import { AcdpMetricsService } from "../acdp-metrics-service";

export class MockedAcdpMetricsService extends AcdpMetricsService {
  mockedApplication: Application;
  mockedApplicationArn: string;
  mockedApplicationTag: string;
  mockedNetUnblendedCurrentMonthCost: string;

  public constructor(
    config?: Config,
    awsCredentialsProvider?: AwsCredentialProvider,
    logger?: LoggerService,
  ) {
    super({
      config: config ?? mockConfigWithoutMultiAccount,
      awsCredentialsProvider: awsCredentialsProvider ?? mockCredentialsProvider,
      logger: logger ?? mockServices.logger.mock(),
    });

    this.mockedApplication = {
      arn: mockedApplicationArn,
      applicationTag: {
        [constants.APP_REGISTRY_AWS_APPLICATION_TAG]: mockedApplicationTag,
      },
    };
    this.mockedApplicationArn = mockedApplicationArn;
    this.mockedApplicationTag = mockedApplicationTag;
    this.mockedNetUnblendedCurrentMonthCost = mockedCurrentMonthCost;
  }

  private areEntitiesEqual(entity: Entity): boolean {
    return JSON.stringify(entity) === JSON.stringify(mockedCatalogEntity);
  }

  public async getApplicationByEntity(entity: Entity): Promise<Application> {
    return this.areEntitiesEqual(entity) ? this.mockedApplication : {};
  }

  public async getApplicationByArn(arn: string): Promise<Application> {
    return arn === mockedApplicationArn ? this.mockedApplication : {};
  }

  public async getNetUnblendedCurrentMonthCost(
    entity: Entity,
    awsApplicationTag: string,
  ): Promise<string> {
    return awsApplicationTag === this.mockedApplicationTag &&
      this.areEntitiesEqual(entity)
      ? this.mockedNetUnblendedCurrentMonthCost
      : "";
  }
}
