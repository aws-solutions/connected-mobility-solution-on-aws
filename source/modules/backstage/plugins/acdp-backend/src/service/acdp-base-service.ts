// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { Logger } from "winston";

import { Entity } from "@backstage/catalog-model";
import { Config } from "@backstage/config";
import { AwsCredentialProvider } from "@backstage/integration-aws-node";

import { EnvironmentVariable } from "@aws-sdk/client-codebuild";
import { SSMClient, GetParameterCommand } from "@aws-sdk/client-ssm";

import { constants, AcdpDeploymentTarget } from "backstage-plugin-acdp-common";

import {
  getDeploymentTargetForEntity,
  getSsmParameterNameForEntityBuildParameters,
} from "./utils";

import { awsApiCallWithErrorHandling } from "../utils";

export interface AcdpBaseServiceOptions {
  config: Config;
  awsCredentialsProvider: AwsCredentialProvider;
  logger: Logger;
  userAgentString: string;
}

export class AcdpBaseService {
  _userAgentString: string;
  _deploymentTargets: AcdpDeploymentTarget[];
  _buildConfigSsmPrefix: string;
  _awsCredentialsProvider: AwsCredentialProvider;
  _logger: Logger;

  constructor(options: AcdpBaseServiceOptions) {
    const { config, awsCredentialsProvider, logger, userAgentString } = options;

    const defaultDeploymentTarget = {
      name: constants.ACDP_DEFAULT_DEPLOYMENT_TARGET,
      awsAccount: config.getString("acdp.deploymentDefaults.accountId"),
      awsRegion: config.getString("acdp.deploymentDefaults.region"),
      codeBuildArn: config.getString(
        "acdp.deploymentDefaults.codeBuildProjectArn",
      ),
    };
    this._deploymentTargets = [defaultDeploymentTarget];
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
    const deploymentTarget = getDeploymentTargetForEntity(
      entity,
      this._deploymentTargets,
    );
    const parameterName = getSsmParameterNameForEntityBuildParameters(
      this._buildConfigSsmPrefix,
      entity,
    );

    const command = new GetParameterCommand({
      Name: parameterName,
      WithDecryption: true,
    });

    const customErrorMessage = "Failed to retrieve build parameters from ssm.";
    const ssmClient = this._getSSMClient(deploymentTarget.awsRegion);
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
