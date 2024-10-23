// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { CatalogClient } from "@backstage/catalog-client";
import { Entity } from "@backstage/catalog-model";

import { MockedAcdpBuildService } from "../../service/mocks";
import { AcdpBuildApi } from "..";
import {
  AcdpBuildProject,
  AcdpBuildProjectBuild,
} from "backstage-plugin-acdp-common";

export class MockedAcdpBuildApi extends AcdpBuildApi {
  public constructor(
    catalogClient: CatalogClient,
    acdpBuildService: MockedAcdpBuildService,
  ) {
    super(catalogClient, acdpBuildService);
  }

  public getProject(): Promise<AcdpBuildProject> {
    return Promise.resolve({
      name: "test-project",
      arn: "arn:aws:codebuild:us-west-2:111111111111:project/test",
      environment: {
        type: "LINUX_CONTAINER",
        image: "aws/codebuild/amazonlinux2-x86_64-standard:3.0",
        computeType: "BUILD_GENERAL1_SMALL",
        privilegedMode: false,
        imagePullCredentialsType: "CODEBUILD",
      },
      created: new Date("2022-05-20T13:58:29.342000-06:00"),
      lastModified: new Date("2022-05-20T13:58:29.342000-06:00"),
    });
  }

  public getBuilds(entity: Entity): Promise<AcdpBuildProjectBuild[]> {
    if (entity === undefined) return Promise.reject();

    return Promise.resolve([
      {
        arn: "arn:aws:codebuild:us-west-2:111111111111:build/test:test",
        buildNumber: 1,
        buildStatus: "SUCCEEDED",
        currentPhase: "COMPLETED",
        endTime: new Date("2022-04-14T23:34:38.397Z"),
        startTime: new Date("2022-04-14T23:31:26.086Z"),
      },
      {
        arn: "arn:aws:codebuild:us-west-2:111111111111:build/test:test",
        buildComplete: true,
        buildNumber: 2,
        buildStatus: "SUCCEEDED",
        currentPhase: "COMPLETED",
        endTime: new Date("2022-04-14T23:34:38.397Z"),
        startTime: new Date("2022-04-14T23:31:26.086Z"),
      },
    ]);
  }

  public startBuild(entity: Entity): Promise<any> {
    return Promise.resolve(entity);
  }

  public getEntity(
    entityRef: string,
    backstageApiToken: string | undefined,
  ): Promise<Entity> {
    return super.getEntity(entityRef, backstageApiToken);
  }
}
