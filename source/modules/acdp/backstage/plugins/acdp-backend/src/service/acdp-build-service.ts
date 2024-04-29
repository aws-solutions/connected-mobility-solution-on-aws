// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { Config } from "@backstage/config";
import { parse } from "@aws-sdk/util-arn-parser";
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

import { AwsCredentialProvider } from "@backstage/integration-aws-node";

import { getLocationForEntity } from "../utils";
import {
  constants,
  AcdpDeploymentTarget,
  AcdpBuildAction,
  BuildSourceConfig,
} from "backstage-plugin-acdp-common";
import { Location } from "@backstage/catalog-client";
import {
  Entity,
  parseLocationRef,
  getEntitySourceLocation,
  getCompoundEntityRef,
  stringifyEntityRef,
  ANNOTATION_SOURCE_LOCATION,
} from "@backstage/catalog-model";
import { InputError } from "@backstage/errors";
import { UrlReader } from "@backstage/backend-common";
import { ScmIntegrations } from "@backstage/integration";
import { Logger } from "winston";
import {
  SSMClient,
  PutParameterCommand,
  GetParameterCommand,
} from "@aws-sdk/client-ssm";
import * as path from "path";

export class AcdpBuildService {
  private reader: UrlReader;
  private integrations: ScmIntegrations;
  private userAgentString: string;
  private deploymentTargets: AcdpDeploymentTarget[];
  private buildParameterSsmPrefix: string;
  private awsCredentialsProvider: AwsCredentialProvider;
  private ssmClient: SSMClient;
  private logger: Logger;

  constructor(options: {
    config: Config;
    reader: UrlReader;
    integrations: ScmIntegrations;
    awsCredentialsProvider: AwsCredentialProvider;
    logger: Logger;
  }) {
    const { config, reader, integrations, awsCredentialsProvider, logger } =
      options;

    const defaultDeploymentTarget = {
      name: constants.ACDP_DEFAULT_DEPLOYMENT_TARGET,
      awsAccount: config.getString("acdp.deploymentDefaults.accountId"),
      awsRegion: config.getString("acdp.deploymentDefaults.region"),
      codeBuildArn: config.getString(
        "acdp.deploymentDefaults.codeBuildProjectArn",
      ),
    };
    this.deploymentTargets = [defaultDeploymentTarget];
    this.buildParameterSsmPrefix = config.getString(
      "acdp.buildConfig.buildConfigStoreSsmPrefix",
    );
    this.userAgentString = config.getString("acdp.metrics.userAgentString");
    this.reader = reader;
    this.integrations = integrations;
    this.awsCredentialsProvider = awsCredentialsProvider;

    this.ssmClient = new SSMClient({
      customUserAgent: this.userAgentString,
      credentialDefaultProvider: () =>
        this.awsCredentialsProvider.sdkCredentialProvider,
    });
    this.logger = logger;
  }

  private getDeploymentTargetForEntity(entity: Entity) {
    const annotations = entity.metadata.annotations!;

    const deploymentTargetName =
      annotations[constants.ACDP_DEPLOYMENT_TARGET_ANNOTATION];

    if (!deploymentTargetName) {
      throw new InputError(
        `No deployment target is set under annotation '${constants.ACDP_DEPLOYMENT_TARGET_ANNOTATION}'`,
      );
    }

    const deploymentTarget = this.deploymentTargets.find(
      (deploymentTarget) => deploymentTarget.name === deploymentTargetName,
    );

    if (!deploymentTarget) {
      throw new InputError(
        `No deployment target found with name '${deploymentTargetName}'`,
      );
    }

    return deploymentTarget;
  }

  private getCodeBuildClient(region: string) {
    return new CodeBuildClient({
      region: region,
      customUserAgent: this.userAgentString,
      credentialDefaultProvider: () =>
        this.awsCredentialsProvider.sdkCredentialProvider,
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
        this.logger.error("Buildspec not found");
        return undefined;
      } else {
        throw err;
      }
    }
  }

  public async getProject(entity: Entity): Promise<Project | undefined> {
    const deploymentTarget = this.getDeploymentTargetForEntity(entity);
    const codeBuildClient = this.getCodeBuildClient(deploymentTarget.awsRegion);
    const { projectName } = this.parseCodeBuildArn(
      deploymentTarget.codeBuildArn,
    );

    const projectQueryResult = await codeBuildClient.send(
      new BatchGetProjectsCommand({
        names: [projectName],
      }),
    );
    return projectQueryResult.projects?.[0];
  }

  public async getBuilds(entity: Entity): Promise<Build[]> {
    const deploymentTarget = this.getDeploymentTargetForEntity(entity);
    const codeBuildClient = this.getCodeBuildClient(deploymentTarget.awsRegion);
    const { projectName } = this.parseCodeBuildArn(
      deploymentTarget.codeBuildArn,
    );

    const buildIds = await codeBuildClient.send(
      new ListBuildsForProjectCommand({
        projectName,
      }),
    );

    let builds: Build[] = [];

    if (buildIds.ids) {
      const output = await codeBuildClient.send(
        new BatchGetBuildsCommand({
          ids: buildIds.ids,
        }),
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

    const deploymentTarget = this.getDeploymentTargetForEntity(entity);
    const codeBuildClient = this.getCodeBuildClient(deploymentTarget.awsRegion);
    const buildspecBody = await this.getBuildspecForAction(action, entity);

    if (buildspecBody === undefined) {
      this.logger.error("No buildspec available for action, can't run build");
      const output: StartBuildCommandOutput = {
        build: undefined,
        $metadata: {},
      };
      return output;
    }

    const storedEnvironmentVariables =
      await this.retrieveBuildEnvironmentVariables(entity);

    const buildSourceConfig = await this.retrieveBuildSourceConfig(entity);

    const environmentVariables =
      this.updateEnvironmentVariablesForDeploymentTarget(
        storedEnvironmentVariables,
        deploymentTarget,
        entity,
      );

    return await codeBuildClient.send(
      new StartBuildCommand({
        projectName: deploymentTarget.codeBuildArn,
        buildspecOverride: buildspecBody,
        environmentVariablesOverride: environmentVariables,
        sourceTypeOverride: buildSourceConfig.sourceType,
        sourceLocationOverride: buildSourceConfig.sourceLocation,
        sourceVersion: buildSourceConfig.sourceVersion,
      }),
    );
  }

  private parseCodeBuildArn(arn: string): {
    accountId: string;
    region: string;
    service: string;
    resource: string;
    projectName: string;
  } {
    const parsedArn = parse(arn);
    const resourceParts = parsedArn.resource.split("/");
    const projectName = resourceParts[1].split(":")[0];

    return { projectName, ...parsedArn };
  }

  public async storeBuildEnvironmentVariables(
    entity: Entity,
    variables: EnvironmentVariable[],
  ) {
    const serializedVariables = JSON.stringify(variables);
    const parameterName =
      this.getSsmParameterNameForEntityBuildParameters(entity);

    const command = new PutParameterCommand({
      Name: parameterName,
      Value: serializedVariables,
      Type: "SecureString",
      Overwrite: true,
    });

    try {
      await this.ssmClient.send(command);
    } catch (error) {
      this.logger.error("Failed to store build parameters in ssm", error);
      throw new Error("Failed to store build parameters");
    }
  }

  private async retrieveBuildEnvironmentVariables(
    entity: Entity,
  ): Promise<EnvironmentVariable[]> {
    const parameterName =
      this.getSsmParameterNameForEntityBuildParameters(entity);

    const command = new GetParameterCommand({
      Name: parameterName,
      WithDecryption: true,
    });

    try {
      const response = await this.ssmClient.send(command);
      if (response.Parameter?.Value) {
        const variables: EnvironmentVariable[] = JSON.parse(
          response.Parameter.Value,
        );
        return variables;
      }
      throw new Error(`Parameter '${parameterName}' not found or has no value`);
    } catch (error) {
      this.logger.error("Failed to retrieve build parameters from ssm", error);
      throw new Error("Failed to retrieve build parameters");
    }
  }

  protected getSsmParameterNameForEntityBuildParameters(entity: Entity) {
    const { kind, namespace, name } = getCompoundEntityRef(entity);
    return path.posix.join(
      this.buildParameterSsmPrefix,
      kind.toLowerCase(),
      namespace.toLowerCase(),
      name.toLowerCase(),
      constants.BUILD_PARAMETER_SSM_POSTFIX,
    );
  }

  protected getSsmParameterNameForEntitySourceConfig(entity: Entity) {
    const { kind, namespace, name } = getCompoundEntityRef(entity);
    return path.posix.join(
      this.buildParameterSsmPrefix,
      kind.toLowerCase(),
      namespace.toLowerCase(),
      name.toLowerCase(),
      constants.BUILD_SOURCE_CONFIG_SSM_POSTFIX,
    );
  }

  private updateEnvironmentVariablesForDeploymentTarget(
    environmentVariables: EnvironmentVariable[],
    deploymentTarget: AcdpDeploymentTarget,
    entity: Entity,
  ) {
    if (!environmentVariables) environmentVariables = [];

    const overrideValues = [
      {
        name: "AWS_ACCOUNT_ID",
        value: deploymentTarget.awsAccount,
      },
      {
        name: "AWS_REGION",
        value: deploymentTarget.awsRegion,
      },
      {
        name: constants.BACKSTAGE_ENTITY_UID_ENVIRONMENT_VARIABLE,
        value: entity.metadata.uid,
      },
      {
        name: "BACKSTAGE_ENTITY_REF",
        value: stringifyEntityRef(entity),
      },
    ];

    for (const variableOverride of overrideValues) {
      const variableIndex = environmentVariables.findIndex(
        (x) => x.name === variableOverride.name,
      );
      if (variableIndex >= 0) {
        environmentVariables[variableIndex].value = variableOverride.value;
      } else {
        environmentVariables.push(variableOverride);
      }
    }

    return environmentVariables;
  }

  public async storeBuildSourceConfig(
    entity: Entity,
    config: BuildSourceConfig,
  ) {
    const serializedConfig = JSON.stringify(config);
    const parameterName = this.getSsmParameterNameForEntitySourceConfig(entity);

    const command = new PutParameterCommand({
      Name: parameterName,
      Value: serializedConfig,
      Type: "SecureString",
      Overwrite: true,
    });

    try {
      await this.ssmClient.send(command);
    } catch (error) {
      this.logger.error("Failed to store build source config in ssm", error);
      throw new Error("Failed to store build source config");
    }
  }

  private async retrieveBuildSourceConfig(
    entity: Entity,
  ): Promise<BuildSourceConfig> {
    const parameterName = this.getSsmParameterNameForEntitySourceConfig(entity);

    const command = new GetParameterCommand({
      Name: parameterName,
      WithDecryption: true,
    });

    try {
      const response = await this.ssmClient.send(command);
      if (response.Parameter?.Value) {
        const storedConfig: BuildSourceConfig = JSON.parse(
          response.Parameter.Value,
        );

        let config: BuildSourceConfig = storedConfig;

        if (
          storedConfig.useEntityAssets === true &&
          entity.metadata.annotations?.[ANNOTATION_SOURCE_LOCATION] !==
            undefined
        ) {
          const catalogItemSourceLocation = removeUrlPrefix(
            entity.metadata.annotations[ANNOTATION_SOURCE_LOCATION],
          );
          const sourceType = getCodeBuildSourceTypeForUrl(
            catalogItemSourceLocation,
          );
          let assetPathCodeBuildLocation: string = catalogItemSourceLocation;
          if (sourceType == SourceType.S3)
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
    } catch (error) {
      this.logger.error(
        "Failed to retrieve build source config from ssm",
        error,
      );
      throw new Error("Failed to retrieve build source config");
    }
  }
}

function removeUrlPrefix(input: string): string {
  return input.replace(/^url:/, "");
}

function getCodeBuildSourceTypeForUrl(url: string): SourceType {
  const githubPattern = /^https?:\/\/(www\.)?github\.com\/.+\/.+$/;
  //NOSONAR
  const s3Pattern =
    /^https?:\/\/s3[\.-](?:[a-z0-9-]+)\.amazonaws\.com\/.+|https?:\/\/[a-z0-9-]+\.s3[\.-](?:[a-z0-9-]+)\.amazonaws\.com\/.+/;

  if (githubPattern.test(url)) {
    return SourceType.GITHUB;
  } else if (s3Pattern.test(url)) {
    return SourceType.S3;
  } else {
    return SourceType.NO_SOURCE;
  }
}

function formatS3UrlToPath(url: string): string {
  const urlObject = new URL(url);

  let bucket: string;
  let path: string = urlObject.pathname.substring(1);

  if (urlObject.hostname.endsWith("s3.amazonaws.com")) {
    bucket = urlObject.hostname.split(".s3.amazonaws.com")[0];
  } else {
    bucket = urlObject.hostname.split(".s3.")[0];
  }

  return `${bucket}/${path}`;
}
