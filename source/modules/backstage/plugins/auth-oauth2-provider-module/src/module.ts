// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {
  authProvidersExtensionPoint,
  createOAuthProviderFactory,
} from "@backstage/plugin-auth-node";
import { oauth2Authenticator } from "@backstage/plugin-auth-backend-module-oauth2-provider";
import {
  createBackendModule,
  coreServices,
} from "@backstage/backend-plugin-api";
import {
  DEFAULT_NAMESPACE,
  stringifyEntityRef,
} from "@backstage/catalog-model";

export const authModuleOAuth2Provider = createBackendModule({
  pluginId: "auth",
  moduleId: "oauth2-provider",
  register(env) {
    env.registerInit({
      deps: {
        logger: coreServices.logger,
        config: coreServices.rootConfig,
        database: coreServices.database,
        discovery: coreServices.discovery,
        auth: coreServices.auth,
        http: coreServices.httpRouter,
        authProviderExtensionPoint: authProvidersExtensionPoint,
      },
      async init({ config, authProviderExtensionPoint }) {
        const additionalScopes = config
          .getOptionalString("auth.config.additionalScopes")
          ?.split(" "); // Additional scopes specified by user during ACDP deployment
        authProviderExtensionPoint.registerProvider({
          providerId: "oauth2",
          factory: createOAuthProviderFactory({
            additionalScopes:
              additionalScopes?.[0] === "cms-unset"
                ? undefined
                : additionalScopes, // Known value for not setting any additional scopes
            authenticator: oauth2Authenticator,
            signInResolver: async (info, ctx) => {
              const {
                profile: { email },
              } = info;
              if (!email) {
                throw new Error("User profile contained no email");
              }

              const [backstageUsername] = email.split("@");

              const userEntityRef = stringifyEntityRef({
                kind: "User",
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
          }),
        });
      },
    });
  },
});
