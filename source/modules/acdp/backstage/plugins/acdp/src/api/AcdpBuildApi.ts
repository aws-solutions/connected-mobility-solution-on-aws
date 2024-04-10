// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {
  IdentityApi,
  ConfigApi,
  createApiRef,
} from "@backstage/core-plugin-api";
import { ResponseError } from "@backstage/errors";
import {
  AcdpBuildAction,
  AcdpBuildProject,
  AcdpBuildProjectBuild,
} from "backstage-plugin-acdp-common";

export const acdpBuildApiRef = createApiRef<AcdpBuildApi>({
  id: "plugin.acdpbuild.service",
});

export interface StartBuildInput {
  entityRef: string;
  action: AcdpBuildAction;
}

export class AcdpBuildApi {
  private readonly configApi: ConfigApi;
  private readonly identityApi: IdentityApi;

  public constructor(options: {
    configApi: ConfigApi;
    identityApi: IdentityApi;
  }) {
    this.configApi = options.configApi;
    this.identityApi = options.identityApi;
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

    return await this.fetch<AcdpBuildProject>(urlSegment);
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

    return await this.fetch<AcdpBuildProjectBuild[]>(urlSegment);
  }

  async startBuild(input: StartBuildInput): Promise<AcdpBuildProjectBuild> {
    return await this.fetch<AcdpBuildProjectBuild>("/startBuild", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(input),
    });
  }

  private async fetch<T = any>(input: string, init?: RequestInit): Promise<T> {
    const baseUrl = `${this.configApi.getString(
      "backend.baseUrl",
    )}/api/acdp-backend`;

    const { token: idToken } = await this.identityApi.getCredentials();

    const headers: HeadersInit = new Headers(init?.headers);
    if (idToken && !headers.has("authorization")) {
      headers.set("authorization", `Bearer ${idToken}`);
    }

    const request = new Request(`${baseUrl}${input}`, {
      ...init,
      headers,
    });

    return fetch(request).then(async (response) => {
      if (!response.ok) {
        throw await ResponseError.fromResponse(response);
      }

      const text = await response.text();
      if (text != undefined && text.length > 0) {
        return JSON.parse(text);
      } else {
        return undefined;
      }
    });
  }
}
