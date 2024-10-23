// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { Logger } from "winston";

import { UrlReader } from "@backstage/backend-common";
import { Location } from "@backstage/catalog-client";
import {
  Entity,
  parseLocationRef,
  getEntitySourceLocation,
  ANNOTATION_SOURCE_LOCATION,
} from "@backstage/catalog-model";
import { Config } from "@backstage/config";
import { InputError } from "@backstage/errors";
import { ScmIntegrations } from "@backstage/integration";
import { AwsCredentialProvider } from "@backstage/integration-aws-node";

import {
  BatchGetBuildsCommand,
  BatchGetProjectsCommand,
  Build,
  CodeBuildClient,
  EnvironmentVariable,
  ListBuildsForProjectCommand,
  Project,
  SourceType,
  StartBuildCommand,
  StartBuildCommandOutput,
} from "@aws-sdk/client-codebuild";
import { PutParameterCommand, GetParameterCommand } from "@aws-sdk/client-ssm";

import {
  constants,
  AcdpBuildAction,
  BuildSourceConfig,
} from "backstage-plugin-acdp-common";

import { awsApiCallWithErrorHandling, getLocationForEntity } from "../utils";
import {
  formatS3UrlToPath,
  getCodeBuildSourceTypeForUrl,
  parseCodeBuildArn,
  removeUrlPrefix,
  getDeploymentTargetForEntity,
  getSsmParameterNameForEntityBuildParameters,
  getSsmParameterNameForEntitySourceConfig,
  updateEnvironmentVariablesForDeploymentTarget,
} from "./utils";
import { AcdpBaseService } from "./acdp-base-service";

export interface AcdpBuildServiceOptions {
  config: Config;
  reader: UrlReader;
  integrations: ScmIntegrations;
  awsCredentialsProvider: AwsCredentialProvider;
  logger: Logger;
}

export class AcdpBuildService extends AcdpBaseService {
  private reader: UrlReader;
  private integrations: ScmIntegrations;

  constructor(options: AcdpBuildServiceOptions) {
    super({
      ...options,
      userAgentString: options.config.getString("acdp.metrics.userAgentString"),
    });
    const { reader, integrations } = options;

    this.reader = reader;
    this.integrations = integrations;
  }

  private getCodeBuildClient(region?: string): CodeBuildClient {
    return new CodeBuildClient({
      region: region,
      customUserAgent: this._userAgentString,
      credentialDefaultProvider: () =>
        this._awsCredentialsProvider.sdkCredentialProvider,
    });
  }

  private async getBuildspecForAction(action: AcdpBuildAction, entity: Entity) {
    const entityAnnotations = entity.metadata.annotations!;

    let actionBuildspecAnnotation: string | undefined = undefined;
    let actionDefaultBuildspecPath: string | undefined = undefined;

    switch (action) {
      case AcdpBuildAction.DEPLOY:
        actionBuildspecAnnotation = constants.ACDP_DEPLOY_BUILDSPEC_ANNOTATION;
        actionDefaultBuildspecPath =
          constants.ACDP_DEFAULT_DEPLOY_BUILDSPEC_LOCATION;
        break;
      case AcdpBuildAction.UPDATE:
        actionBuildspecAnnotation = constants.ACDP_UPDATE_BUILDSPEC_ANNOTATION;
        actionDefaultBuildspecPath =
          constants.ACDP_DEFAULT_UPDATE_BUILDSPEC_LOCATION;
        break;
      case AcdpBuildAction.TEARDOWN:
        actionBuildspecAnnotation =
          constants.ACDP_TEARDOWN_BUILDSPEC_ANNOTATION;
        actionDefaultBuildspecPath =
          constants.ACDP_DEFAULT_TEARDOWN_BUILDSPEC_LOCATION;
        break;
      default:
        throw new InputError("Invalid ACDP Build Action");
    }

    let buildspecPath = entityAnnotations[actionBuildspecAnnotation];
    if (!buildspecPath) {
      buildspecPath = actionDefaultBuildspecPath;
    }

    const sourceLocation = getEntitySourceLocation(entity);
    if (!sourceLocation.target.endsWith("/")) sourceLocation.target += "/";
    const location = parseLocationRef(buildspecPath) as Location;

    const resolvedLocation = getLocationForEntity(
      location,
      sourceLocation.target,
      this.integrations,
      false,
    );

    try {
      const buildspecBody = await this.reader.readUrl(resolvedLocation.target);
      return (await buildspecBody.buffer()).toString();
    } catch (err: any) {
      if (err.name === "NoSuchKey") {
        this._logger.error("Buildspec not found");
        return undefined;
      }

      throw err;
    }
  }

  public async getProject(entity: Entity): Promise<Project | undefined> {
    const deploymentTarget = getDeploymentTargetForEntity(
      entity,
      this._deploymentTargets,
    );
    const codeBuildClient = this.getCodeBuildClient(deploymentTarget.awsRegion);
    const { projectName } = parseCodeBuildArn(deploymentTarget.codeBuildArn);

    const projectQueryResult = await awsApiCallWithErrorHandling(
      () =>
        codeBuildClient.send(
          new BatchGetProjectsCommand({
            names: [projectName],
          }),
        ),
      `Could not get projects with project name: ${projectName}`,
      this._logger,
    );
    return projectQueryResult.projects?.[0];
  }

  public async getBuilds(entity: Entity): Promise<Build[]> {
    const deploymentTarget = getDeploymentTargetForEntity(
      entity,
      this._deploymentTargets,
    );
    const codeBuildClient = this.getCodeBuildClient(deploymentTarget.awsRegion);
    const { projectName } = parseCodeBuildArn(deploymentTarget.codeBuildArn);

    const buildIds = await awsApiCallWithErrorHandling(
      () =>
        codeBuildClient.send(
          new ListBuildsForProjectCommand({
            projectName,
          }),
        ),
      `Could not list builds with project name: ${projectName}`,
      this._logger,
    );

    let builds: Build[] = [];

    if (buildIds.ids) {
      const output = await awsApiCallWithErrorHandling(
        () =>
          codeBuildClient.send(
            new BatchGetBuildsCommand({
              ids: buildIds.ids,
            }),
          ),
        `Could not get builds with build ids: ${buildIds.ids}`,
        this._logger,
      );
      builds = output.builds ?? [];
    }

    const filteredBuilds = builds.filter((build: Build) => {
      const entityUidEnvVar = build.environment?.environmentVariables?.find(
        (environmentVariable) =>
          environmentVariable.name ===
          constants.BACKSTAGE_ENTITY_UID_ENVIRONMENT_VARIABLE,
      );
      return entityUidEnvVar?.value === entity.metadata.uid;
    });

    return filteredBuilds;
  }

  public async startBuild(options: {
    entity: Entity;
    action: AcdpBuildAction;
  }) {
    const { entity, action } = options;

    const deploymentTarget = getDeploymentTargetForEntity(
      entity,
      this._deploymentTargets,
    );
    const codeBuildClient = this.getCodeBuildClient(deploymentTarget.awsRegion);
    const buildspecBody = await this.getBuildspecForAction(action, entity);

    if (buildspecBody === undefined) {
      this._logger.error("No buildspec available for action, can't run build");
      const output: StartBuildCommandOutput = {
        build: undefined,
        $metadata: {},
      };
      return output;
    }

    const storedEnvironmentVariables =
      await this._retrieveBuildEnvironmentVariables(entity);

    const buildSourceConfig = await this.retrieveBuildSourceConfig(entity);

    const environmentVariables = updateEnvironmentVariablesForDeploymentTarget(
      deploymentTarget,
      entity,
      storedEnvironmentVariables,
    );

    return await awsApiCallWithErrorHandling(
      () =>
        codeBuildClient.send(
          new StartBuildCommand({
            projectName: deploymentTarget.codeBuildArn,
            buildspecOverride: buildspecBody,
            environmentVariablesOverride: environmentVariables,
            sourceTypeOverride: buildSourceConfig.sourceType,
            sourceLocationOverride: buildSourceConfig.sourceLocation,
            sourceVersion: buildSourceConfig.sourceVersion,
          }),
        ),
      `Could not start build for project name: ${deploymentTarget.codeBuildArn}`,
      this._logger,
    );
  }

  public async storeBuildEnvironmentVariables(
    entity: Entity,
    variables: EnvironmentVariable[],
  ) {
    const deploymentTarget = getDeploymentTargetForEntity(
      entity,
      this._deploymentTargets,
    );
    const serializedVariables = JSON.stringify(variables);
    const parameterName = getSsmParameterNameForEntityBuildParameters(
      this._buildConfigSsmPrefix,
      entity,
    );

    const command = new PutParameterCommand({
      Name: parameterName,
      Value: serializedVariables,
      Type: "SecureString",
      Overwrite: true,
    });

    const ssmClient = this._getSSMClient(deploymentTarget.awsRegion);
    await awsApiCallWithErrorHandling(
      () => ssmClient.send(command),
      `Failed to store build environment variables in ssm with parameter name: ${parameterName}`,
      this._logger,
    );
  }

  public async storeBuildSourceConfig(
    entity: Entity,
    config: BuildSourceConfig,
  ) {
    const deploymentTarget = getDeploymentTargetForEntity(
      entity,
      this._deploymentTargets,
    );
    const parameterName = getSsmParameterNameForEntitySourceConfig(
      this._buildConfigSsmPrefix,
      entity,
    );
    const serializedConfig = JSON.stringify(config);

    const command = new PutParameterCommand({
      Name: parameterName,
      Value: serializedConfig,
      Type: "SecureString",
      Overwrite: true,
    });

    const ssmClient = this._getSSMClient(deploymentTarget.awsRegion);
    await awsApiCallWithErrorHandling(
      () => ssmClient.send(command),
      `Failed to store build source config in ssm with parameter name: ${parameterName}.`,
      this._logger,
    );
  }

  private async retrieveBuildSourceConfig(
    entity: Entity,
  ): Promise<BuildSourceConfig> {
    const deploymentTarget = getDeploymentTargetForEntity(
      entity,
      this._deploymentTargets,
    );
    const parameterName = getSsmParameterNameForEntitySourceConfig(
      this._buildConfigSsmPrefix,
      entity,
    );

    const command = new GetParameterCommand({
      Name: parameterName,
      WithDecryption: true,
    });

    const ssmClient = this._getSSMClient(deploymentTarget.awsRegion);
    const response = await awsApiCallWithErrorHandling(
      () => ssmClient.send(command),
      `Failed to get build source config from ssm with parameter name: ${parameterName}`,
      this._logger,
    );
    if (response.Parameter?.Value) {
      const storedConfig: BuildSourceConfig = JSON.parse(
        response.Parameter.Value,
      );

      let config: BuildSourceConfig = storedConfig;

      if (
        storedConfig.useEntityAssets === true &&
        entity.metadata.annotations?.[ANNOTATION_SOURCE_LOCATION] !== undefined
      ) {
        const catalogItemSourceLocation = removeUrlPrefix(
          entity.metadata.annotations[ANNOTATION_SOURCE_LOCATION],
        );
        const sourceType = getCodeBuildSourceTypeForUrl(
          catalogItemSourceLocation,
        );
        let assetPathCodeBuildLocation: string = catalogItemSourceLocation;
        if (sourceType === SourceType.S3)
          assetPathCodeBuildLocation = formatS3UrlToPath(
            catalogItemSourceLocation,
          );

        config = {
          useEntityAssets: true,
          sourceType: sourceType,
          sourceLocation: assetPathCodeBuildLocation,
        };
      }

      return config;
    }
    throw new Error(`Parameter '${parameterName}' not found or has no value`);
  }
}
