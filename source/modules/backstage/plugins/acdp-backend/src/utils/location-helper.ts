// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { ScmIntegrationRegistry } from "@backstage/integration";
import { Location } from "@backstage/catalog-client";

import { resolveSafeChildPath } from "@backstage/backend-common";

import { InputError } from "@backstage/errors";

import * as path from "path";

const resolvePath = (
  baseUrl: string,
  assetPath: string,
  allowUnsafeAccess: boolean,
) => {
  if (allowUnsafeAccess) {
    // skips relative path check for local filesystem access
    return path.resolve(baseUrl, assetPath);
  }

  return resolveSafeChildPath(baseUrl, assetPath);
};

const transformDirLocation = (
  baseUrl: string,
  dirAnnotation: Location,
  scmIntegrations: ScmIntegrationRegistry,
  allowUnsafeAccess: boolean,
): Location => {
  let locationType = "url";
  if (baseUrl.startsWith("file://")) locationType = "file";

  switch (locationType) {
    case "url": {
      const target = scmIntegrations.resolveUrl({
        url: dirAnnotation.target,
        base: baseUrl,
      });

      return {
        id: "",
        type: "url",
        target,
      };
    }

    case "file": {
      // only permit targets in the same folder as the target of the `file` location
      const target = resolvePath(
        path.dirname(baseUrl.slice("file://".length)),
        dirAnnotation.target,
        allowUnsafeAccess,
      );

      return {
        id: "",
        type: "dir",
        target,
      };
    }

    default:
      throw new InputError(`Unable to resolve location type ${locationType}`);
  }
};

export const getLocationForEntity = (
  location: Location,
  baseUrl: string,
  scmIntegration: ScmIntegrationRegistry,
  allowUnsafeAccess: boolean,
): Location => {
  switch (location.type) {
    case "url":
      return location;
    case "dir":
      return transformDirLocation(
        baseUrl,
        location,
        scmIntegration,
        allowUnsafeAccess,
      );
    default:
      throw new Error(`Invalid reference location ${location.type}`);
  }
};
