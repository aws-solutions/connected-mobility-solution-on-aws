// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { createApiRef } from "@backstage/core-plugin-api";
import {
  AcdpBuildAction,
  AcdpBuildProject,
  AcdpBuildProjectBuild,
} from "backstage-plugin-acdp-common";

import { AcdpBaseApi, AcdpBaseApiInput } from "./AcdpBaseApi";

export const acdpBuildApiRef = createApiRef<AcdpBuildApi>({
  id: "plugin.acdpbuild.service",
});

export interface StartBuildInput {
  entityRef: string;
  action: AcdpBuildAction;
}

export class AcdpBuildApi extends AcdpBaseApi {
  public constructor(options: AcdpBaseApiInput) {
    super(options);
  }

  async getProject({
    entityRef,
  }: {
    entityRef: string;
  }): Promise<AcdpBuildProject> {
    const searchParams = new URLSearchParams({
      entityRef: entityRef,
    });
    const urlSegment = `/project?${searchParams}`;

    return await this._fetch<AcdpBuildProject>(urlSegment);
  }

  async listBuilds({
    entityRef,
  }: {
    entityRef: string;
  }): Promise<AcdpBuildProjectBuild[]> {
    const searchParams = new URLSearchParams({
      entityRef: entityRef,
    });
    const urlSegment = `/builds?${searchParams}`;

    return await this._fetch<AcdpBuildProjectBuild[]>(urlSegment);
  }

  async startBuild(input: StartBuildInput): Promise<AcdpBuildProjectBuild> {
    return await this._fetch<AcdpBuildProjectBuild>("/start-build", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(input),
    });
  }
}
