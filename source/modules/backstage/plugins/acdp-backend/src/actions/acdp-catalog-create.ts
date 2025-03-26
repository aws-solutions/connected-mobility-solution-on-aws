// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import * as path from "path";
import * as yaml from "yaml";
import { z } from "zod";

import {
  PutObjectCommand,
  PutObjectCommandInput,
  S3Client,
} from "@aws-sdk/client-s3";

import {
  AuthService,
  DiscoveryService,
  LoggerService,
  resolveSafeChildPath,
  UrlReaderService,
} from "@backstage/backend-plugin-api";
import { CatalogClient, Location } from "@backstage/catalog-client";
import {
  CompoundEntityRef,
  DEFAULT_NAMESPACE,
  ANNOTATION_SOURCE_LOCATION,
  Entity,
  parseLocationRef,
} from "@backstage/catalog-model";
import { Config } from "@backstage/config";
import { InputError } from "@backstage/errors";
import { ScmIntegrations } from "@backstage/integration";
import { DefaultAwsCredentialsManager } from "@backstage/integration-aws-node";

import {
  createTemplateAction,
  fetchContents,
  ActionContext,
} from "@backstage/plugin-scaffolder-node";
import { Publisher, PublisherBase } from "@backstage/plugin-techdocs-node";
import { JsonObject } from "@backstage/types";

import { constants } from "backstage-plugin-acdp-common";

import {
  AwsS3Helper,
  getLocationForEntity,
  awsApiCallWithErrorHandling,
} from "../utils";

interface CatalogConfig {
  bucketName: string;
  region: string;
  catalogPrefix: string;
  catalogItemAssetsPath: string;
  allowUnsafeAccess: boolean;
}

interface CtxInput extends JsonObject {
  componentId: string;
  assetsSourcePath?: string;
  docsSiteSourcePath?: string;
  entity: any;
}

interface AcdpCatalogCreateActionInput {
  config: Config;
  reader: UrlReaderService;
  integrations: ScmIntegrations;
  catalogClient: CatalogClient;
  discovery: DiscoveryService;
  auth: AuthService;
  logger: LoggerService;
}

const copyDocsAssetsToCatalog = async (options: {
  techdocsPublisher: PublisherBase;
  catalogConfig: CatalogConfig;
  catalogCreateInput: AcdpCatalogCreateActionInput;
  ctx: ActionContext<CtxInput, JsonObject>;
  entity: Entity;
}) => {
  const { techdocsPublisher, catalogConfig, catalogCreateInput, ctx, entity } =
    options;

  const docsTargetPath = "./techdocs";
  const docsTmpPath = resolveSafeChildPath(ctx.workspacePath, docsTargetPath);

  const templateBaseUrl = ctx.templateInfo!.baseUrl!;
  let fetchBaseUrl = templateBaseUrl;
  if (
    catalogConfig.allowUnsafeAccess &&
    templateBaseUrl.startsWith("file://")
  ) {
    fetchBaseUrl = "file:///"; // allow access to full local filesystem for local development
  }

  ctx.logger.info("Starting: Fetching docs from source location");

  const location = parseLocationRef(ctx.input.docsSiteSourcePath!) as Location;

  const resolvedLocation = getLocationForEntity(
    location,
    templateBaseUrl,
    catalogCreateInput.integrations,
    catalogConfig.allowUnsafeAccess,
  );

  await fetchContents({
    reader: catalogCreateInput.reader,
    integrations: catalogCreateInput.integrations,
    baseUrl: fetchBaseUrl,
    fetchUrl: resolvedLocation.target,
    outputPath: docsTmpPath,
    token: ctx.input.token?.toString(),
  });
  ctx.logger.info("Finished: Fetching docs from source location");
  ctx.logger.info("Starting: Publishing docs to techdocs asset location");
  await techdocsPublisher.publish({
    entity: entity,
    directory: docsTmpPath,
  });
  ctx.logger.info("Finished: Publishing docs to techdocs asset location");
};

const copyAssetsToCatalog = async (options: {
  s3Client: S3Client;
  catalogConfig: CatalogConfig;
  catalogCreateInput: AcdpCatalogCreateActionInput;
  ctx: ActionContext<CtxInput, JsonObject>;
  catalogEntityPathPrefix: string;
  entity: Entity;
}) => {
  const {
    s3Client,
    catalogConfig,
    catalogCreateInput,
    ctx,
    catalogEntityPathPrefix,
    entity,
  } = options;

  const s3Helper = new AwsS3Helper({
    s3Client: s3Client,
    bucketName: catalogConfig.bucketName,
    logger: ctx.logger,
  });

  const assetsTargetPath = "./assets";

  const assetsTmpPath = resolveSafeChildPath(
    ctx.workspacePath,
    assetsTargetPath,
  );

  const templateBaseUrl = ctx.templateInfo!.baseUrl!;

  let fetchBaseUrl = templateBaseUrl;
  if (
    catalogConfig.allowUnsafeAccess &&
    templateBaseUrl.startsWith("file://")
  ) {
    fetchBaseUrl = "file:///"; // allow access to full local filesystem for local development
  }

  const location = parseLocationRef(ctx.input.assetsSourcePath!) as Location;
  const resolvedLocation = getLocationForEntity(
    location,
    templateBaseUrl,
    catalogCreateInput.integrations,
    catalogConfig.allowUnsafeAccess,
  );
  await fetchContents({
    reader: catalogCreateInput.reader,
    integrations: catalogCreateInput.integrations,
    baseUrl: fetchBaseUrl,
    fetchUrl: resolvedLocation.target,
    outputPath: assetsTmpPath,
    // token: ctx.input.token, #This is added in next patch version of the fetchContents func...uncomment this on next lib bump
  });

  const assetsUploadPathPrefix = path.join(
    catalogEntityPathPrefix,
    catalogConfig.catalogItemAssetsPath,
  );

  ctx.logger.debug(`Uploading assets to: ${assetsUploadPathPrefix}`);
  ctx.logger.info(`Finding and deleting existing assets from catalog`);
  const existingCatalogObjects = await s3Helper.getAllObjectsFromBucket(
    assetsUploadPathPrefix,
  );
  s3Helper.deleteObjectsFromBucket(existingCatalogObjects);

  ctx.logger.info(`Uploading assets to catalog`);
  s3Helper.uploadFilesToBucket(entity, assetsTmpPath, assetsUploadPathPrefix);
};

const writeCatalogItemToS3 = async (options: {
  s3Client: S3Client;
  catalogConfig: CatalogConfig;
  catalogEntityPathPrefix: string;
  ctx: ActionContext<CtxInput, JsonObject>;
}) => {
  const {
    s3Client,
    catalogConfig,
    catalogEntityPathPrefix: catalogEntityS3KeyPrefix,
    ctx,
  } = options;

  const catalogInfoS3Key = `${catalogEntityS3KeyPrefix}/catalog-info.yaml`;
  const assetsS3Key = `${catalogEntityS3KeyPrefix}/${catalogConfig.catalogItemAssetsPath}`;
  const catalogAssetsPathUrl = `https://${catalogConfig.bucketName}.s3.${catalogConfig.region}.amazonaws.com/${assetsS3Key}`;
  const catalogInfoUrl = `https://${catalogConfig.bucketName}.s3.${catalogConfig.region}.amazonaws.com/${catalogInfoS3Key}`;
  ctx.logger.info(
    `Writing catalog-info to ${catalogConfig.bucketName}/${catalogInfoS3Key}`,
  );

  // Inject required annotations into catalog-info.yaml

  if (ctx.input.docsSiteSourcePath !== undefined) {
    ctx.input.entity.metadata.annotations["aws.amazon.com/techdocs-builder"] =
      "external";
    ctx.input.entity.metadata.annotations["backstage.io/techdocs-ref"] =
      "dir:.";
  }

  ctx.input.entity.metadata.annotations["aws.amazon.com/template-entity-ref"] =
    ctx.templateInfo?.entityRef;

  ctx.input.entity.metadata.annotations[constants.ACDP_ASSETS_REF] =
    `dir:${path.join(".", catalogConfig.catalogItemAssetsPath)}`;

  ctx.input.entity.metadata.annotations[constants.ACDP_ASSETS_STORED] = (
    ctx.input.assetsSourcePath !== undefined
  ).toString();

  ctx.input.entity.metadata.annotations[ANNOTATION_SOURCE_LOCATION] =
    `url:${catalogAssetsPathUrl}`;

  const putCatalogEntityInput: PutObjectCommandInput = {
    Body: yaml.stringify(ctx.input.entity),
    Bucket: catalogConfig.bucketName,
    Key: catalogInfoS3Key,
  };
  const putCatalogEntityResp = await awsApiCallWithErrorHandling(
    () => s3Client.send(new PutObjectCommand(putCatalogEntityInput)),
    `Could not put catalog item in s3 bucket with bucket name: ${catalogConfig.bucketName} and key: ${catalogInfoS3Key}`,
    ctx.logger,
  );

  if (putCatalogEntityResp.ETag !== undefined) {
    ctx.logger.info("Successfully created catalog item");
    ctx.logger.debug(
      `Successfully created s3 object for catalog item: s3://${putCatalogEntityInput.Bucket}/${putCatalogEntityInput.Key}`,
    );
    ctx.output("catalogItemS3Url", catalogInfoUrl);
    ctx.output(
      "catalogItemS3Uri",
      `s3://${catalogConfig.bucketName}/${catalogInfoS3Key}`,
    );
  }
};

export const createAcdpCatalogCreateAction = async (
  options: AcdpCatalogCreateActionInput,
) => {
  const { config, catalogClient, discovery, logger, auth } = options;

  const awsCredentialsManager = DefaultAwsCredentialsManager.fromConfig(config);
  const credentialProvider =
    await awsCredentialsManager.getCredentialProvider();
  const userAgentString = config.getString("acdp.metrics.userAgentString");

  const catalogConfig: CatalogConfig = {
    bucketName: config.getString("acdp.s3Catalog.bucketName"),
    region: config.getString("acdp.s3Catalog.region"),
    catalogPrefix: config.getString("acdp.s3Catalog.prefix"),
    catalogItemAssetsPath:
      config.getOptionalString("acdp.s3Catalog.catalogItemAssetsPath") ??
      "assets/",
    allowUnsafeAccess:
      config.getOptionalBoolean("acdp.allow-unsafe-local-dir-access") ?? false,
  };

  if (!catalogConfig.catalogItemAssetsPath.endsWith("/")) {
    logger.error(
      "acdp.s3Catalog.catalogItemAssetsPath must have a trailing slash",
    );
    throw new Error("Invalid acdp.s3Catalog.catalogItemAssetsPath");
  }

  const techdocsPublisher = await Publisher.fromConfig(config, {
    logger: logger,
    discovery: discovery,
  });
  await techdocsPublisher.getReadiness();

  return createTemplateAction<CtxInput>({
    id: "aws:acdp:catalog:create",
    description:
      "Writes the catalog-info.yaml and copies assets for your template to the backend s3 bucket",
    schema: {
      input: z.object({
        componentId: z
          .string()
          .describe(
            "The unique component id which is used for the catalog-info name",
          ),
        assetsSourcePath: z
          .string()
          .optional()
          .describe(
            "optional: path to the assets used by this component to copy into the catalog item's assets folder",
          ),
        docsSiteSourcePath: z
          .string()
          .optional()
          .describe(
            "optional: path to the techdocs site folder to copy into the techdocs' assets store. Techdocs must be configured for this to work.",
          ),
        entity: z
          .record(z.any())
          .describe(
            "YAML body for the catalog-info.yaml content. It will automatically be updated with ACDP Metadata",
          ),
      }),
      output: {
        type: "object",
        properties: {
          s3Url: {
            title: "S3 URL Path file was uploaded to",
            type: "string",
          },
          s3Uri: {
            title: "S3 URI Path file was uploaded to",
            type: "string",
          },
        },
      },
    },

    async handler(ctx) {
      if (
        ctx.templateInfo === undefined ||
        ctx.templateInfo.baseUrl === undefined
      ) {
        throw new InputError("Unable to read template info");
      }

      const { token } = await auth.getPluginRequestToken({
        onBehalfOf: await auth.getOwnServiceCredentials(),
        targetPluginId: "catalog",
      });

      const compoundEntity: CompoundEntityRef = {
        kind: ctx.input.entity.kind.toLowerCase(),
        namespace: (
          ctx.input.entity.metadata?.namespace ?? DEFAULT_NAMESPACE
        ).toLowerCase(),
        name: ctx.input.entity.metadata.name.toLowerCase(),
      };
      const entity = {
        kind: compoundEntity.kind,
        metadata: {
          namespace: compoundEntity.namespace,
          name: compoundEntity.name,
        },
      } as Entity;

      // Check if a registered entity already exists
      const existingEntity = await catalogClient.getEntityByRef(
        compoundEntity,
        {
          token: token,
        },
      );
      if (existingEntity)
        throw new Error(
          `The entity ref ${existingEntity.metadata.namespace}/${existingEntity.kind}/${existingEntity.metadata.name} already exists`,
        );

      const catalogEntityPathPrefix = `${catalogConfig.catalogPrefix}/${compoundEntity.namespace}/${compoundEntity.kind}/${compoundEntity.name}`;

      const s3Client = new S3Client({
        region: catalogConfig.region,
        customUserAgent: userAgentString,
        credentialDefaultProvider: () =>
          credentialProvider.sdkCredentialProvider,
      });

      if (ctx.input.docsSiteSourcePath !== undefined) {
        await copyDocsAssetsToCatalog({
          techdocsPublisher: techdocsPublisher,
          catalogConfig: catalogConfig,
          catalogCreateInput: options,
          ctx: ctx,
          entity: entity,
        });
      } else {
        ctx.logger.info(
          "Skipping techdocs upload...docsSiteSourcePath is unset",
        );
      }

      if (ctx.input.assetsSourcePath !== undefined) {
        await copyAssetsToCatalog({
          s3Client: s3Client,
          catalogConfig: catalogConfig,
          catalogCreateInput: options,
          ctx: ctx,
          catalogEntityPathPrefix: catalogEntityPathPrefix,
          entity: entity,
        });
      } else {
        ctx.logger.info("Skipping assets upload...assetsSourcePath is unset");
      }

      await writeCatalogItemToS3({
        s3Client: s3Client,
        catalogConfig: catalogConfig,
        ctx: ctx,
        catalogEntityPathPrefix: catalogEntityPathPrefix,
      });
    },
  });
};
