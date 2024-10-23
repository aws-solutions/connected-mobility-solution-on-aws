// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { Logger } from "winston";

import { Entity } from "@backstage/catalog-model";
import { Config } from "@backstage/config";
import { AwsCredentialProvider } from "@backstage/integration-aws-node";

import {
  Application,
  GetApplicationCommand,
  ServiceCatalogAppRegistryClient,
} from "@aws-sdk/client-service-catalog-appregistry";

import {
  GetCostAndUsageCommand,
  CostExplorerClient,
  GetCostAndUsageCommandInput,
} from "@aws-sdk/client-cost-explorer";

import { constants } from "backstage-plugin-acdp-common";

import { getDeploymentTargetForEntity, getRegionFromArn } from "./utils";
import { AcdpBaseService } from "./acdp-base-service";

import { awsApiCallWithErrorHandling } from "../utils";

export interface AcdpMetricsServiceOptions {
  config: Config;
  awsCredentialsProvider: AwsCredentialProvider;
  logger: Logger;
}

export class AcdpMetricsService extends AcdpBaseService {
  constructor(options: AcdpMetricsServiceOptions) {
    super({
      ...options,
      userAgentString: options.config.getString("acdp.metrics.userAgentString"),
    });
  }

  private getAppRegistryClient(
    region?: string,
  ): ServiceCatalogAppRegistryClient {
    return new ServiceCatalogAppRegistryClient({
      region: region,
      customUserAgent: this._userAgentString,
      credentialDefaultProvider: () =>
        this._awsCredentialsProvider.sdkCredentialProvider,
    });
  }

  private getCostExplorerClient(region?: string): CostExplorerClient {
    return new CostExplorerClient({
      region: region,
      customUserAgent: this._userAgentString,
      credentialDefaultProvider: () =>
        this._awsCredentialsProvider.sdkCredentialProvider,
    });
  }

  public async getApplicationByEntity(entity: Entity): Promise<Application> {
    const deploymentTarget = getDeploymentTargetForEntity(
      entity,
      this._deploymentTargets,
    );
    const appRegistryClient = this.getAppRegistryClient(
      deploymentTarget.awsRegion,
    );

    const storedEnvironmentVariables =
      await this._retrieveBuildEnvironmentVariables(entity);

    // ACDP build action sets a MODULE_STACK_NAME environment variable in the CodeBuild environment, and stores this variable in SSM. This is then used by the deploy buildspecs as the stack name.
    // This can be used to determine the application name, but could be incompatible with third-party modules that don't follow this convention.
    const moduleStackName = storedEnvironmentVariables.find(
      (variable) =>
        variable.name === constants.MODULE_STACK_NAME_ENVIRONMENT_VARIABLE,
    )?.value;

    const applicationName = `${moduleStackName}-${deploymentTarget.awsRegion}-${deploymentTarget.awsAccount}`;

    const getApplicationOutput = await awsApiCallWithErrorHandling(
      () =>
        appRegistryClient.send(
          new GetApplicationCommand({
            application: applicationName, // Name, ID, or Arn
          }),
        ),
      `Could not get application from entity with application name: ${applicationName}.`,
      this._logger,
    );

    const application: Application = {
      arn: getApplicationOutput.arn,
      applicationTag: getApplicationOutput.applicationTag,
    };

    return application;
  }

  public async getApplicationByArn(arn: string): Promise<Application> {
    const region = getRegionFromArn(arn);
    const appRegistryClient = this.getAppRegistryClient(region);

    const getApplicationOutput = await awsApiCallWithErrorHandling(
      () =>
        appRegistryClient.send(
          new GetApplicationCommand({
            application: arn, // Name, ID, or Arn
          }),
        ),
      `Could not get application with application arn: ${arn}.`,
      this._logger,
    );

    const application: Application = {
      arn: getApplicationOutput.arn,
      applicationTag: getApplicationOutput.applicationTag,
    };

    return application;
  }

  public async getNetUnblendedCurrentMonthCost(
    entity: Entity,
    awsApplicationTag: string,
  ): Promise<string> {
    const deploymentTarget = getDeploymentTargetForEntity(
      entity,
      this._deploymentTargets,
    );
    const costExplorerClient = this.getCostExplorerClient(
      deploymentTarget.awsRegion,
    );

    const firstDayOfMonth = new Date();
    firstDayOfMonth.setDate(1);
    const lastDayOfMonth = new Date(
      firstDayOfMonth.getFullYear(),
      firstDayOfMonth.getMonth() + 1,
      1,
    ); // Get first day of next month
    lastDayOfMonth.setDate(lastDayOfMonth.getDate() - 1); // Subtract one day to get last day of current month

    const getCostAndUsageCommandInput: GetCostAndUsageCommandInput = {
      TimePeriod: {
        Start: firstDayOfMonth.toISOString().split("T")[0], // Format: YYYY-MM-DD
        End: lastDayOfMonth.toISOString().split("T")[0],
      },
      Granularity: "MONTHLY",
      Metrics: ["NetUnblendedCost"],
      Filter: {
        Tags: {
          Key: constants.APP_REGISTRY_AWS_APPLICATION_TAG,
          Values: [awsApplicationTag],
          MatchOptions: ["EQUALS"],
        },
      },
    };

    const getCostAndUsageOutput = await awsApiCallWithErrorHandling(
      () =>
        costExplorerClient.send(
          new GetCostAndUsageCommand(getCostAndUsageCommandInput),
        ),
      `Could not get cost and usage for awsApplicationTag: ${awsApplicationTag}`,
      this._logger,
    );

    return (
      getCostAndUsageOutput.ResultsByTime?.[0]?.Total?.NetUnblendedCost
        .Amount ?? ""
    );
  }
}
