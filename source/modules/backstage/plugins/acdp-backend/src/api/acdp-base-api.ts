// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { LoggerService } from "@backstage/backend-plugin-api";
import { CatalogClient } from "@backstage/catalog-client";
import { Entity } from "@backstage/catalog-model";
import { NotFoundError } from "@backstage/errors";

export interface AcdpBaseApiInput {
  catalogClient: CatalogClient;
}

export class AcdpBaseApi {
  _logger: LoggerService;
  _catalogClient: CatalogClient;

  public constructor(catalogClient: CatalogClient, logger: LoggerService) {
    this._catalogClient = catalogClient;
    this._logger = logger;
  }

  public async getEntity(
    entityRef: string,
    backstageApiToken: string | undefined,
  ): Promise<Entity> {
    const getEntityErrorMessage = `Could not find Entity for ref: '${entityRef}'`;
    const entity = await this._catalogClient.getEntityByRef(entityRef, {
      token: backstageApiToken,
    });

    if (entity === undefined) {
      this._logger.error(getEntityErrorMessage);
      throw new NotFoundError(getEntityErrorMessage);
    }

    return entity;
  }
}
