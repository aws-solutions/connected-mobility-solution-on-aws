// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { stringifyEntityRef } from "@backstage/catalog-model";

import { AcdpBuildAction } from "backstage-plugin-acdp-common";

import { AcdpBuildApi } from ".";
import {
  mockCodeBuildEntity,
  mockGlobalFetch,
  mockAcdpBaseApiInput,
  baseUrl,
} from "../mocks";

const acdpBuildApiClient = new AcdpBuildApi(mockAcdpBaseApiInput);

let mockedFetch: jest.SpyInstance;
beforeEach(() => {
  mockedFetch = mockGlobalFetch();
});

afterEach(() => {
  jest.clearAllMocks();
});

describe("AcdpBuildApi", () => {
  it("should getProject", async () => {
    await acdpBuildApiClient.getProject({
      entityRef: stringifyEntityRef(mockCodeBuildEntity),
    });

    const fetchCall = mockedFetch.mock.calls[0][0].valueOf() as Request;
    expect(fetchCall.method).toEqual("GET");
    expect(fetchCall.url).toEqual(
      `${baseUrl}/api/acdp-backend/project?entityRef=component%3Aacdp-build%2Fcms-sample`,
    );
  });

  it("should listBuilds", async () => {
    await acdpBuildApiClient.listBuilds({
      entityRef: stringifyEntityRef(mockCodeBuildEntity),
    });

    const fetchCall = mockedFetch.mock.calls[0][0].valueOf() as Request;
    expect(fetchCall.method).toEqual("GET");
    expect(fetchCall.url).toEqual(
      `${baseUrl}/api/acdp-backend/builds?entityRef=component%3Aacdp-build%2Fcms-sample`,
    );
  });

  it("should startDeployBuild", async () => {
    const startBuildInput = {
      entityRef: stringifyEntityRef(mockCodeBuildEntity),
      action: AcdpBuildAction.DEPLOY,
    };
    await acdpBuildApiClient.startBuild(startBuildInput);

    const fetchCall = mockedFetch.mock.calls[0][0].valueOf() as Request;
    expect(fetchCall.method).toEqual("POST");
    expect(fetchCall.url).toEqual(`${baseUrl}/api/acdp-backend/start-build`);
    expect(await fetchCall.json()).toStrictEqual(startBuildInput);
  });

  it("should startUpdateBuild", async () => {
    const startBuildInput = {
      entityRef: stringifyEntityRef(mockCodeBuildEntity),
      action: AcdpBuildAction.UPDATE,
    };
    await acdpBuildApiClient.startBuild(startBuildInput);

    const fetchCall = mockedFetch.mock.calls[0][0].valueOf() as Request;
    expect(fetchCall.method).toEqual("POST");
    expect(fetchCall.url).toEqual(`${baseUrl}/api/acdp-backend/start-build`);
    expect(await fetchCall.json()).toStrictEqual(startBuildInput);
  });

  it("should startTeardownBuild", async () => {
    const startBuildInput = {
      entityRef: stringifyEntityRef(mockCodeBuildEntity),
      action: AcdpBuildAction.TEARDOWN,
    };
    await acdpBuildApiClient.startBuild(startBuildInput);

    const fetchCall = mockedFetch.mock.calls[0][0].valueOf() as Request;
    expect(fetchCall.method).toEqual("POST");
    expect(fetchCall.url).toEqual(`${baseUrl}/api/acdp-backend/start-build`);
    expect(await fetchCall.json()).toStrictEqual(startBuildInput);
  });
});
