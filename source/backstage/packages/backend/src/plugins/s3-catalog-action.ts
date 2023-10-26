// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { Config } from '@backstage/config';
import { createTemplateAction } from '@backstage/plugin-scaffolder-node';
import { v4 as uuidv4 } from 'uuid';
import * as yaml from 'yaml';
import { z } from 'zod';

import { DefaultAwsCredentialsManager } from '@backstage/integration-aws-node';

import {
  PutObjectCommand,
  PutObjectCommandInput,
  S3Client,
} from '@aws-sdk/client-s3';

export const createNewCatalogInfoAction = (options: { config: Config }) => {
  const { config } = options;
  const awsCredentialsManager = DefaultAwsCredentialsManager.fromConfig(config);

  const bucketName = config.getString('s3-catalog.bucketName');
  const region = config.getString('s3-catalog.region');
  const catalogPrefix = config.getString('s3-catalog.prefix');

  return createTemplateAction({
    id: 'aws:s3:catalog:write',
    description:
      'Writes the catalog-info.yaml for your template to the backend s3 bucket',
    schema: {
      input: z.object({
        componentId: z
          .string()
          .describe(
            'The unique component id which is used for the catalog-info name',
          ),
        entity: z
          .record(z.any())
          .describe('YAML body for the catalog-info.yaml content'),
      }),
      output: {
        type: 'object',
        properties: {
          s3Url: {
            title: 'S3 URL Path file was upload to',
            type: 'string',
          },
          s3Uri: {
            title: 'S3 URI Path file was upload to',
            type: 'string',
          },
        },
      },
    },

    async handler(ctx) {
      const creds = await awsCredentialsManager.getCredentialProvider();

      const client = new S3Client({
        region: region,
        customUserAgent: 'aws-s3-upload-backstage',
        credentialDefaultProvider: () => creds.sdkCredentialProvider,
      });

      const catalogUUID = uuidv4();

      const keyPath = `${catalogPrefix}/catalog-info-${ctx.input.componentId}-${catalogUUID}.yaml`;
      const input: PutObjectCommandInput = {
        Body: yaml.stringify(ctx.input.entity),
        Bucket: bucketName,
        Key: keyPath,
      };

      const resp = await client.send(new PutObjectCommand(input));

      const s3Endpoint = `s3.${region}.amazonaws.com`;

      if (resp.ETag !== undefined) {
        ctx.logger.info(
          `Successfully created s3 object s3://${input.Bucket}/${input.Key}`,
        );
        ctx.output('s3Url', `https://${bucketName}.${s3Endpoint}/${keyPath}`);
        ctx.output('s3Uri', `s3://${bucketName}/${keyPath}`);
      }
    },
  });
};
