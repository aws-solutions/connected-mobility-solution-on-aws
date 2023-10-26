// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {
  createRouter,
  defaultAuthProviderFactories,
} from '@backstage/plugin-auth-backend';
import { Router } from 'express';
import { PluginEnvironment } from '../types';
import { createCognitoProvider } from '../cognito/provider';
import {
  DEFAULT_NAMESPACE,
  stringifyEntityRef,
} from '@backstage/catalog-model';

export default async function createPlugin(
  env: PluginEnvironment,
): Promise<Router> {
  return await createRouter({
    logger: env.logger,
    config: env.config,
    database: env.database,
    discovery: env.discovery,
    tokenManager: env.tokenManager,
    tokenFactoryAlgorithm: 'RS256',
    providerFactories: {
      ...defaultAuthProviderFactories,
      cognito: createCognitoProvider({
        logger: env.logger,
        signIn: {
          resolver: async (info, ctx) => {
            const {
              profile: { email },
            } = info;
            if (!email) {
              throw new Error('User profile contained no email');
            }

            const [backstageUsername] = email.split('@');

            const userEntityRef = stringifyEntityRef({
              kind: 'User',
              name: backstageUsername,
              namespace: DEFAULT_NAMESPACE,
            });

            return ctx.issueToken({
              claims: {
                sub: userEntityRef, // The user's own identity
                ent: [userEntityRef], // A list of identities that the user claims ownership through
              },
            });
          },
        },
      }),
    },
  });
}
