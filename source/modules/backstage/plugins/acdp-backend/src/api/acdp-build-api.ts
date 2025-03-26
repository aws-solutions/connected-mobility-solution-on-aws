// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { CatalogClient } from "@backstage/catalog-client";
import { Entity } from "@backstage/catalog-model";
import {
  AcdpBuildAction,
  AcdpBuildProject,
  AcdpBuildProjectBuild,
} from "backstage-plugin-acdp-common";

import { AcdpBaseApi } from "./acdp-base-api";
import { AcdpBuildService } from "../service/acdp-build-service";

export class AcdpBuildApi extends AcdpBaseApi {
  private acdpBuildService: AcdpBuildService;

  public constructor(
    catalogClient: CatalogClient,
    acdpBuildService: AcdpBuildService,
  ) {
    super(catalogClient, acdpBuildService._logger);
    this.acdpBuildService = acdpBuildService;
  }

  public async getProject(): Promise<AcdpBuildProject | undefined> {
    const codeBuildProject = await this.acdpBuildService.getProject();

    return codeBuildProject
      ? {
          name: codeBuildProject.name,
          arn: codeBuildProject.arn,
        }
      : undefined;
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

    return build
      ? {
          id: build.id,
          arn: build.arn,
          buildNumber: build.buildNumber,
          startTime: build.startTime,
          endTime: build.endTime,
          projectName: build.currentPhase,
        }
      : {};
  }
}
