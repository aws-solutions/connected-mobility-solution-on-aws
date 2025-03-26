// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import crypto from "crypto";
import fetch from "node-fetch";
import * as yaml from "yaml";

import {
  PutObjectCommand,
  PutObjectCommandInput,
  S3Client,
} from "@aws-sdk/client-s3";

import {
  createBackendModule,
  coreServices,
} from "@backstage/backend-plugin-api";
import {
  ANNOTATION_LOCATION,
  ANNOTATION_ORIGIN_LOCATION,
  Entity,
  stringifyEntityRef,
} from "@backstage/catalog-model";
import { DefaultAwsCredentialsManager } from "@backstage/integration-aws-node";
import {
  authProvidersExtensionPoint,
  createOAuthProviderFactory,
} from "@backstage/plugin-auth-node";
import { oauth2Authenticator } from "@backstage/plugin-auth-backend-module-oauth2-provider";

// If the email contains any disallowed values, they are stripped, and the username is appended with a hash.
// If the email contains multiple sections separated by "+" signs, each is filtered, pieced back together
// using a dash, and the username is appended with a hash.
export const generateUsername = (email: string): string => {
  const atIndex = email.indexOf("@");
  if (atIndex === -1) {
    throw new Error("Invalid email address format.");
  }
  const localPart = email.substring(0, atIndex);

  /* defined by backstage: https://github.com/backstage/backstage/blob/master/docs/architecture-decisions/adr002-default-catalog-file-format.md#name */
  const filterAllowed = (str: string): string =>
    str.replace(/[^a-zA-Z0-9._-]/g, "");

  let username: string;

  if (localPart.includes("+")) {
    const parts = localPart.split("+").map(filterAllowed);
    const filteredLocalParts = parts.join("-");
    const hashDigest = crypto
      .createHash("sha256")
      .update(localPart)
      .digest("hex")
      .slice(0, 8);

    username = `${filteredLocalParts}-${hashDigest}`;
  } else {
    const filtered = filterAllowed(localPart);
    if (filtered !== localPart) {
      const hashDigest = crypto
        .createHash("sha256")
        .update(localPart)
        .digest("hex")
        .slice(0, 8);
      username = `${filtered}-${hashDigest}`;
    } else {
      username = filtered;
    }
  }

  return username;
};

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
      async init({
        auth,
        config,
        discovery,
        logger,
        authProviderExtensionPoint,
      }) {
        logger.info(
          "Initializing OAuth2.0 provider module, extension of the auth plugin.",
        );

        // If additional scopes were provided during ACDP deployment, split them into an array for the provider factory.
        const additionalScopes = config
          .getOptionalString("auth.config.additionalScopes")
          ?.split(" ");

        logger.info(
          "Registering oauth2 provider with custom sign-in resolver.",
        );
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
                throw new Error("User profile contained no email.");
              }

              const backstageUsername = generateUsername(email);

              // Construct known user entity format for checking/inserting into catalog.
              const userEntity: Entity = {
                apiVersion: "backstage.io/v1alpha1",
                kind: "User",
                metadata: {
                  name: backstageUsername,
                  namespace: "acdp",
                },
              };
              const userEntityRef = stringifyEntityRef(userEntity);

              // Check if user already has an existing User entity ref in the S3 catalog,
              // or if we need to create one.
              let result = undefined;
              try {
                const existingCatalogUser = await ctx.findCatalogUser({
                  entityRef: userEntityRef,
                });

                // Catalog user entity already exists, continue sign-in.
                logger.info(
                  `${existingCatalogUser.entity.metadata.name} exists in the catalog. Signing in as catalog user.`,
                );
                result = await ctx.signInWithCatalogUser({
                  entityRef: userEntityRef,
                });
              } catch (catalogUserError: any) {
                // Catalog user entity does not exist, create user entity in S3 and register
                // the location in the catalog before signing in.
                logger.info(
                  `${userEntity.metadata.name} not found in catalog. Creating and registering catalog entity before signing in.`,
                );

                const bucketName = config.getString(
                  "acdp.s3Catalog.bucketName",
                );
                const region = config.getString("acdp.s3Catalog.region");
                const customUserAgent = config.getString(
                  "acdp.metrics.userAgentString",
                );
                const catalogPrefix = config.getString("acdp.s3Catalog.prefix");
                const catalogInfoS3Key = `${catalogPrefix}/${userEntity.metadata.namespace?.toLowerCase()}/${userEntity.kind.toLowerCase()}/${userEntity.metadata.name.toLowerCase()}/catalog-info.yaml`;
                const catalogInfoS3Url = `https://${bucketName}.s3.${region}.amazonaws.com/${catalogInfoS3Key}`;

                logger.info(
                  `Writing ${userEntity.metadata.name} catalog-info to ${bucketName}/${catalogInfoS3Key}`,
                );

                // Add location metadata to the new User entity pointing to the S3 source location.
                userEntity.metadata.annotations = {
                  [ANNOTATION_LOCATION]: catalogInfoS3Url,
                  [ANNOTATION_ORIGIN_LOCATION]: catalogInfoS3Url,
                };

                // Add user entity spec data.
                userEntity.spec = {
                  profile: {
                    email: email,
                  },
                  memberOf: [],
                };

                // Write User entity catalog item to the S3 bucket.
                const awsCredentialsManager =
                  DefaultAwsCredentialsManager.fromConfig(config);
                const credentialProvider =
                  await awsCredentialsManager.getCredentialProvider();

                const s3Client = new S3Client({
                  region: region,
                  customUserAgent: customUserAgent,
                  credentialDefaultProvider: () =>
                    credentialProvider.sdkCredentialProvider,
                });

                const putCatalogUserEntityInput: PutObjectCommandInput = {
                  Body: yaml.stringify(userEntity),
                  Bucket: bucketName,
                  Key: catalogInfoS3Key,
                };

                try {
                  await s3Client.send(
                    new PutObjectCommand(putCatalogUserEntityInput),
                  );
                } catch (s3ClientError: any) {
                  logger.error(
                    `Could not put catalog item in s3 bucket with bucket name: ${bucketName} and key: ${catalogInfoS3Key}. Error: ${s3ClientError}`,
                  );
                  if (typeof s3ClientError.statusCode === "number") {
                    throw new Error(
                      `Error while calling AWS API. Status Code: ${s3ClientError.statusCode}`,
                    );
                  } else {
                    throw new Error(
                      "Unexpected error while calling AWS API. Status code unknown.",
                    );
                  }
                }

                // Register the new user entity location so the catalog will immediately discover it.
                const catalogBaseUrl = await discovery.getBaseUrl("catalog");
                const locationsUrl = `${catalogBaseUrl}/locations`;
                const newLocationData = {
                  type: "url",
                  target: catalogInfoS3Url,
                };

                let response = undefined;
                try {
                  const { token: catalogToken } =
                    await auth.getPluginRequestToken({
                      onBehalfOf: await auth.getOwnServiceCredentials(),
                      targetPluginId: "catalog",
                    });
                  response = await fetch(locationsUrl, {
                    method: "POST",
                    headers: {
                      "Content-Type": "application/json",
                      ...(catalogToken && {
                        Authorization: `Bearer ${catalogToken}`,
                      }),
                    },
                    body: JSON.stringify(newLocationData),
                  });

                  if (!response?.ok && !(response.status === 409)) {
                    logger.error(
                      `${catalogInfoS3Url} entity location failed to register: ${await response.text()}`,
                    );
                    throw new Error(
                      "Response error occurred during fetch call to catalog/locations API.",
                    );
                  }
                } catch (catalogApiError: any) {
                  logger.error(
                    `Error during fetch call to catalog API: ${catalogApiError}`,
                  );
                  throw new Error(
                    "Unexpected error occurred during fetch call to catalog/locations API.",
                  );
                }

                // Finally, sign-in.
                logger.info(
                  `${catalogInfoS3Url} entity location successfully registered in catalog. Performing initial sign-in via temporary token.`,
                );
                result = await ctx.issueToken({
                  claims: {
                    sub: userEntityRef, // The user's own identity.
                    ent: [userEntityRef], // A list of identities that the user claims ownership through.
                  },
                });
              }

              return result;
            },
          }),
        });
      },
    });
  },
});
