// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { IdentityApi, ConfigApi } from "@backstage/core-plugin-api";
import { ResponseError } from "@backstage/errors";

export interface AcdpBaseApiInput {
  configApi: ConfigApi;
  identityApi: IdentityApi;
}

export class AcdpBaseApi {
  private readonly configApi: ConfigApi;
  private readonly identityApi: IdentityApi;

  public constructor(options: AcdpBaseApiInput) {
    this.configApi = options.configApi;
    this.identityApi = options.identityApi;
  }

  async _fetch<T = any>(input: string, init?: RequestInit): Promise<T> {
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
      if (text !== undefined && text.length > 0) {
        return JSON.parse(text);
      }

      return undefined;
    });
  }
}
