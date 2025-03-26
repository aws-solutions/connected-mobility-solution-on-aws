// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { Entity } from "@backstage/catalog-model";
import { Config } from "@backstage/config";
import { AwsCredentialProvider } from "@backstage/integration-aws-node";
import { LoggerService } from "@backstage/backend-plugin-api/index";

import { EnvironmentVariable } from "@aws-sdk/client-codebuild";
import { SSMClient, GetParameterCommand } from "@aws-sdk/client-ssm";

import { AcdpDeploymentTarget } from "backstage-plugin-acdp-common";

import { getSsmParameterNameForEntityBuildParameters } from "./utils";

import { awsApiCallWithErrorHandling } from "../utils";

export interface AcdpBaseServiceOptions {
  config: Config;
  awsCredentialsProvider: AwsCredentialProvider;
  logger: LoggerService;
  userAgentString: string;
}

export class AcdpBaseService {
  _userAgentString: string;
  _defaultDeploymentTarget: AcdpDeploymentTarget;
  _buildConfigSsmPrefix: string;
  _awsCredentialsProvider: AwsCredentialProvider;
  _logger: LoggerService;

  constructor(options: AcdpBaseServiceOptions) {
    const { config, awsCredentialsProvider, logger, userAgentString } = options;

    this._defaultDeploymentTarget = {
      awsAccountId: config.getString("acdp.deploymentDefaults.accountId"),
      awsRegion: config.getString("acdp.deploymentDefaults.region"),
      codeBuildArn: config.getString(
        "acdp.deploymentDefaults.codeBuildProjectArn",
      ),
    };
    this._buildConfigSsmPrefix = config.getString(
      "acdp.buildConfig.buildConfigStoreSsmPrefix",
    );
    this._userAgentString = userAgentString;
    this._awsCredentialsProvider = awsCredentialsProvider;
    this._logger = logger;
  }

  _getSSMClient(region?: string): SSMClient {
    return new SSMClient({
      region: region,
      customUserAgent: this._userAgentString,
      credentialDefaultProvider: () =>
        this._awsCredentialsProvider.sdkCredentialProvider,
    });
  }

  async _retrieveBuildEnvironmentVariables(
    entity: Entity,
  ): Promise<EnvironmentVariable[]> {
    const parameterName = getSsmParameterNameForEntityBuildParameters(
      this._buildConfigSsmPrefix,
      entity,
    );

    const command = new GetParameterCommand({
      Name: parameterName,
      WithDecryption: true,
    });

    const customErrorMessage = "Failed to retrieve build parameters from ssm.";
    const ssmClient = this._getSSMClient(
      this._defaultDeploymentTarget.awsRegion,
    );
    const response = await awsApiCallWithErrorHandling(
      () => ssmClient.send(command),
      customErrorMessage,
      this._logger,
    );
    if (response.Parameter?.Value) {
      const variables: EnvironmentVariable[] = JSON.parse(
        response.Parameter.Value,
      );
      return variables;
    }
    throw new Error(`Parameter '${parameterName}' not found or has no value`);
  }
}
