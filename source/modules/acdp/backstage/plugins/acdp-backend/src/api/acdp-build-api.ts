// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { AcdpBuildService } from "../service/acdp-build-service";
import { CatalogClient } from "@backstage/catalog-client";
import { Entity } from "@backstage/catalog-model";
import { NotFoundError } from "@backstage/errors";
import {
  AcdpBuildAction,
  AcdpBuildProject,
  AcdpBuildProjectBuild,
} from "backstage-plugin-acdp-common";

export class AcdpBuildApi {
  private catalogClient: CatalogClient;
  private acdpBuildService: AcdpBuildService;

  public constructor(
    catalogClient: CatalogClient,
    acdpBuildService: AcdpBuildService,
  ) {
    this.catalogClient = catalogClient;
    this.acdpBuildService = acdpBuildService;
  }

  public async getProject(
    entity: Entity,
  ): Promise<AcdpBuildProject | undefined> {
    const codeBuildProject = await this.acdpBuildService.getProject(entity);

    if (codeBuildProject === undefined) return undefined;

    return {
      name: codeBuildProject.name,
      arn: codeBuildProject.arn,
    };
  }

  public async getBuilds(entity: Entity): Promise<AcdpBuildProjectBuild[]> {
    const codeBuildProjectBuilds =
      await this.acdpBuildService.getBuilds(entity);

    return codeBuildProjectBuilds.map((build) => {
      return {
        id: build.id,
        arn: build.arn,
        buildNumber: build.buildNumber,
        startTime: build.startTime,
        endTime: build.endTime,
        currentPhase: build.currentPhase,
        buildStatus: build.buildStatus,
        projectName: build.projectName,
      };
    });
  }

  public async startBuild(
    entity: Entity,
    action: AcdpBuildAction,
  ): Promise<AcdpBuildProjectBuild> {
    const startBuildResponse = await this.acdpBuildService.startBuild({
      entity: entity,
      action: action,
    });

    const build = startBuildResponse.build;

    if (build === undefined) return {};

    return {
      id: build.id,
      arn: build.arn,
      buildNumber: build.buildNumber,
      startTime: build.startTime,
      endTime: build.endTime,
      projectName: build.currentPhase,
    };
  }

  public async getEntity(
    entityRef: string,
    backstageApiToken: string | undefined,
  ): Promise<Entity> {
    const entity = await this.catalogClient.getEntityByRef(entityRef, {
      token: backstageApiToken,
    });

    if (entity === undefined)
      throw new NotFoundError(`Could not find Entity for ref: '${entityRef}'`);

    return entity;
  }
}
