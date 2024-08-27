// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {
  ApiRef,
  BackstageIdentityApi,
  OAuthApi,
  ProfileInfoApi,
  SessionApi,
  createApiRef,
} from "@backstage/core-plugin-api";

export const oauth2ApiRef: ApiRef<
  OAuthApi & ProfileInfoApi & BackstageIdentityApi & SessionApi
> = createApiRef({
  id: "auth.oauth2", // Can be anything, but must be unique
});
