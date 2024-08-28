// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { stringifyEntityRef } from "@backstage/catalog-model";
import { AcdpBuildApi } from ".";
import { MockConfigApi } from "@backstage/test-utils";
import { mockCodeBuildEntity } from "../mocks/mocksCodeBuild";
import { AcdpBuildAction } from "backstage-plugin-acdp-common";

const baseUrl = "https://example.com";

const acdpBuildApiClient = new AcdpBuildApi({
  configApi: new MockConfigApi({
    backend: {
      baseUrl,
    },
  }),
  identityApi: {
    getBackstageIdentity: jest.fn(),
    getCredentials: jest.fn().mockReturnValue({ token: "test" }),
    getProfileInfo: jest.fn(),
    signOut: jest.fn(),
  },
});

let mockedFetch: jest.SpyInstance;
beforeEach(() => {
  mockedFetch = jest.spyOn(global, "fetch").mockImplementation((input) => {
    const { status, ok } = (input.valueOf() as Request).url.includes(
      "arn=bad-arn",
    )
      ? { status: 404, ok: false }
      : { status: 200, ok: true };
    return Promise.resolve({
      text: () => Promise.resolve(""),
      status,
      ok,
    } as Response);
  });
});

afterEach(() => {
  jest.clearAllMocks();
});

describe("test", () => {
  it("should getProject", async () => {
    await acdpBuildApiClient.getProject({
      entityRef: stringifyEntityRef(mockCodeBuildEntity),
    });

    const fetchCall = mockedFetch.mock.calls[0][0].valueOf() as Request;
    expect(fetchCall.method).toEqual("GET");
    expect(fetchCall.url).toEqual(
      `${baseUrl}/api/acdp-backend/project?entityRef=component%3Aacdp%2Fcms-sample`,
    );
  });

  it("should listBuilds", async () => {
    await acdpBuildApiClient.listBuilds({
      entityRef: stringifyEntityRef(mockCodeBuildEntity),
    });

    const fetchCall = mockedFetch.mock.calls[0][0].valueOf() as Request;
    expect(fetchCall.method).toEqual("GET");
    expect(fetchCall.url).toEqual(
      `${baseUrl}/api/acdp-backend/builds?entityRef=component%3Aacdp%2Fcms-sample`,
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
    expect(fetchCall.url).toEqual(`${baseUrl}/api/acdp-backend/startBuild`);
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
    expect(fetchCall.url).toEqual(`${baseUrl}/api/acdp-backend/startBuild`);
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
    expect(fetchCall.url).toEqual(`${baseUrl}/api/acdp-backend/startBuild`);
    expect(await fetchCall.json()).toStrictEqual(startBuildInput);
  });
});
