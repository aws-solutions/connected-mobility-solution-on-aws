// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { SourceType } from "@aws-sdk/client-codebuild";

import {
  AuthService,
  LoggerService,
  UrlReaderService,
} from "@backstage/backend-plugin-api";
import { CatalogClient } from "@backstage/catalog-client";
import { Entity, parseEntityRef } from "@backstage/catalog-model";
import { Config } from "@backstage/config";
import { ScmIntegrations } from "@backstage/integration";
import { DefaultAwsCredentialsManager } from "@backstage/integration-aws-node";
import { createTemplateAction } from "@backstage/plugin-scaffolder-node";

import { AcdpBuildAction, constants } from "backstage-plugin-acdp-common";

import { AcdpBuildService } from "../service/acdp-build-service";
import { OperationalMetrics } from "../utils/operational-metrics";

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export const createAcdpConfigureAction = async (options: {
  config: Config;
  reader: UrlReaderService;
  integrations: ScmIntegrations;
  catalogClient: CatalogClient;
  auth: AuthService;
  logger: LoggerService;
}) => {
  const { config, reader, integrations, catalogClient, logger, auth } = options;

  const awsCredentialsManager = DefaultAwsCredentialsManager.fromConfig(config);
  const awsCredentialProvider =
    await awsCredentialsManager.getCredentialProvider();

  const acdpBuildService = new AcdpBuildService({
    config: config,
    reader: reader,
    integrations: integrations,
    awsCredentialsProvider: awsCredentialProvider,
    logger: logger,
    operationalMetrics: new OperationalMetrics({
      logger,
      config,
    }),
  });

  return createTemplateAction({
    id: "aws:acdp:configure",
    description:
      "Registers and configures the catalog item to be able to run ACDP builds",
    schema: {
      input: {
        entityRef: (z: any) => z.string(),
        sourceOverrideConfig: (z: any) =>
          z
            .object({
              sourceType: (z2: any) =>
                z2.enum(["S3", "GITHUB", "CODECOMMIT", "NO_SOURCE"]),
              sourceLocation: (z2: any) => z2.string(),
              sourceVersion: (z2: any) => z2.string().optional(),
            })
            .optional(),
        buildParameters: (z: any) =>
          z
            .array({
              name: (z2: any) => z2.string(),
              value: (z2: any) => z2.string(),
            })
            .optional(),
      },
      output: {
        codeBuildProjectArn: (z: any) => z.string(),
      },
    },

    handler: async (ctx) => {
      const { token } = await auth.getPluginRequestToken({
        onBehalfOf: await auth.getOwnServiceCredentials(),
        targetPluginId: "catalog",
      });
      const entityRef = parseEntityRef(ctx.input.entityRef);

      let entity: Entity | undefined = undefined;
      const maxRetries = 10;
      let tryCount = 0;
      do {
        if (tryCount > 0) await sleep(5000);
        tryCount++;
        entity = await catalogClient.getEntityByRef(entityRef, {
          token: token,
        });
      } while (entity === undefined && tryCount < maxRetries);

      if (entity === undefined) {
        throw new Error(
          "Failed to configure ACDP build due to entity not yet showing up in the catalog",
        );
      }

      const environmentVariables = [
        {
          name: constants.MODULE_STACK_NAME_ENVIRONMENT_VARIABLE,
          value: `${entity?.metadata.namespace}-${entity?.metadata.name}`,
        },
      ];

      if (ctx.input.buildParameters)
        environmentVariables.push(...ctx.input.buildParameters);

      await acdpBuildService.storeBuildEnvironmentVariables(
        entity,
        environmentVariables,
      );

      if (!ctx.input.sourceOverrideConfig) {
        await acdpBuildService.storeBuildSourceConfig(entity, {
          useEntityAssets:
            entity.metadata?.annotations?.[constants.ACDP_ASSETS_STORED] ===
            "true",
        });
      } else {
        await acdpBuildService.storeBuildSourceConfig(entity, {
          useEntityAssets: false,
          sourceType: ctx.input.sourceOverrideConfig.sourceType as SourceType,
          sourceLocation: ctx.input.sourceOverrideConfig.sourceLocation,
          sourceVersion: ctx.input.sourceOverrideConfig.sourceVersion,
        });
      }

      const shouldDeployAnnotation =
        entity?.metadata?.annotations![
          constants.ACDP_DEPLOY_ON_CREATE_ANNOTATION
        ];

      if (shouldDeployAnnotation === "true") {
        await acdpBuildService.startBuild({
          entity: entity,
          action: AcdpBuildAction.DEPLOY,
        });
      }
    },
  });
};
