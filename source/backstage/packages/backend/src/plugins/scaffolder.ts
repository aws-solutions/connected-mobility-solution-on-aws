// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { CatalogClient } from '@backstage/catalog-client';
import { Router } from 'express';
import type { PluginEnvironment } from '../types';
import { ScmIntegrations } from '@backstage/integration';
import {
  createBuiltinActions,
  createRouter,
} from '@backstage/plugin-scaffolder-backend';
import { createAwsProtonServiceAction } from '@aws/aws-proton-backend-plugin-for-backstage';
import { createNewCatalogInfoAction } from './s3-catalog-action';
import { createNewYamlFileAction } from './yaml-fs-writer';

export default async function createPlugin(
  env: PluginEnvironment,
): Promise<Router> {
  const catalogClient = new CatalogClient({
    discoveryApi: env.discovery,
  });

  const integrations = ScmIntegrations.fromConfig(env.config);

  const builtInActions = createBuiltinActions({
    integrations,
    catalogClient,
    reader: env.reader,
    config: env.config,
  });

  const actions = [
    ...builtInActions,
    createAwsProtonServiceAction({ config: env.config }),
    createNewCatalogInfoAction({ config: env.config }),
    createNewYamlFileAction()
  ];

  return await createRouter({
    logger: env.logger,
    config: env.config,
    database: env.database,
    reader: env.reader,
    catalogClient,
    actions,
    identity: env.identity,
    permissions: env.permissions,
  });
}
