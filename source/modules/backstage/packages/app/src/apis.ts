// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {
  ScmIntegrationsApi,
  scmIntegrationsApiRef,
  ScmAuth,
} from "@backstage/integration-react";
import {
  AnyApiFactory,
  configApiRef,
  createApiFactory,
  discoveryApiRef,
  oauthRequestApiRef,
} from "@backstage/core-plugin-api";
import { OAuth2 } from "@backstage/core-app-api";
import { UserIcon } from "@backstage/core-components";
import { oauth2ApiRef } from "./apis/oauth2Api";

export const apis: AnyApiFactory[] = [
  createApiFactory({
    api: oauth2ApiRef,
    deps: {
      discoveryApi: discoveryApiRef,
      oauthRequestApi: oauthRequestApiRef,
      configApi: configApiRef,
    },
    factory: ({ discoveryApi, oauthRequestApi, configApi }) =>
      OAuth2.create({
        configApi,
        discoveryApi,
        oauthRequestApi,
        provider: {
          id: "oauth2", // This must match the id given to the SignInPage providers option and in the app-config auth section
          title: "OAuth 2.0 Provider",
          icon: UserIcon,
        },
        environment: configApi.getString("auth.environment"),
        defaultScopes: ["openid", "profile", "email"],
        popupOptions: {
          size: {
            width: 500,
            height: 500,
          },
        },
      }),
  }),
  createApiFactory({
    api: scmIntegrationsApiRef,
    deps: { configApi: configApiRef },
    factory: ({ configApi }) => ScmIntegrationsApi.fromConfig(configApi),
  }),
  ScmAuth.createDefaultApiFactory(),
];
