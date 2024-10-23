// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

/*
 * Copyright 2022 The Backstage Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

jest.mock("@backstage/plugin-catalog-react", () => ({
  useEntityList: jest.fn(),
}));

jest.mock("../PartnerOfferingGroup/PartnerOfferingGroup", () => ({
  PartnerOfferingGroup: jest.fn(() => null),
}));

import React from "react";
import { useEntityList } from "@backstage/plugin-catalog-react";
import { PartnerOfferingGroups } from "./PartnerOfferingGroups";
import { renderInTestApp, TestApiProvider } from "@backstage/test-utils";
import { errorApiRef } from "@backstage/core-plugin-api";
import { PartnerOfferingGroup } from "../PartnerOfferingGroup";

describe("PartnerOfferingGroups", () => {
  beforeEach(() => jest.clearAllMocks());

  it("should return progress if the hook is loading", async () => {
    (useEntityList as jest.Mock).mockReturnValue({ loading: true });

    const { findByTestId } = await renderInTestApp(
      <TestApiProvider apis={[[errorApiRef, {}]]}>
        <PartnerOfferingGroups groups={[]} />
      </TestApiProvider>,
    );

    expect(await findByTestId("progress")).toBeInTheDocument();
  });

  it("should use the error api if there is an error with the retrieval of entitylist", async () => {
    const mockError = new Error("tings went poop");
    (useEntityList as jest.Mock).mockReturnValue({
      error: mockError,
    });
    const errorApi = {
      post: jest.fn(),
    };
    await renderInTestApp(
      <TestApiProvider apis={[[errorApiRef, errorApi]]}>
        <PartnerOfferingGroups groups={[]} />
      </TestApiProvider>,
    );

    expect(errorApi.post).toHaveBeenCalledWith(mockError);
  });

  it("should return a no partner offerings message if entities is unset", async () => {
    (useEntityList as jest.Mock).mockReturnValue({
      entities: null,
      loading: false,
      error: null,
    });

    const { findByText } = await renderInTestApp(
      <TestApiProvider apis={[[errorApiRef, {}]]}>
        <PartnerOfferingGroups groups={[]} />
      </TestApiProvider>,
    );

    expect(await findByText(/No partner offerings found/)).toBeInTheDocument();
  });

  it("should return a no partner offerings message if entities has no values in it", async () => {
    (useEntityList as jest.Mock).mockReturnValue({
      entities: [],
      loading: false,
      error: null,
    });

    const { findByText } = await renderInTestApp(
      <TestApiProvider apis={[[errorApiRef, {}]]}>
        <PartnerOfferingGroups groups={[]} />
      </TestApiProvider>,
    );

    expect(await findByText(/No partner offerings found/)).toBeInTheDocument();
  });

  it("should call the partner offerings group with the components", async () => {
    const mockEntities = [
      {
        apiVersion: "aws.amazon.com/v1beta1",
        kind: "PartnerOffering",
        metadata: {
          name: "t1",
        },
        spec: {},
      },
      {
        apiVersion: "aws.amazon.com/v1beta1",
        kind: "PartnerOffering",
        metadata: {
          name: "t2",
        },
        spec: {},
      },
    ];

    (useEntityList as jest.Mock).mockReturnValue({
      entities: mockEntities,
      loading: false,
      error: null,
    });

    await renderInTestApp(
      <TestApiProvider apis={[[errorApiRef, {}]]}>
        <PartnerOfferingGroups
          groups={[{ title: "all", filter: () => true }]}
        />
      </TestApiProvider>,
    );

    expect(PartnerOfferingGroup).toHaveBeenCalledWith(
      expect.objectContaining({
        partnerOfferings: mockEntities.map((partnerOffering) =>
          expect.objectContaining({ partnerOffering }),
        ),
      }),
      {},
    );
  });

  it("should apply the filter for each group", async () => {
    const mockEntities = [
      {
        apiVersion: "aws.amazon.com/v1beta1",
        kind: "PartnerOffering",
        metadata: {
          name: "t1",
        },
        spec: {},
      },
      {
        apiVersion: "aws.amazon.com/v1beta1",
        kind: "PartnerOffering",
        metadata: {
          name: "t2",
        },
        spec: {},
      },
    ];

    (useEntityList as jest.Mock).mockReturnValue({
      entities: mockEntities,
      loading: false,
      error: null,
    });

    await renderInTestApp(
      <TestApiProvider apis={[[errorApiRef, {}]]}>
        <PartnerOfferingGroups
          groups={[{ title: "all", filter: (e) => e.metadata.name === "t1" }]}
        />
      </TestApiProvider>,
    );

    expect(PartnerOfferingGroup).toHaveBeenCalledWith(
      expect.objectContaining({
        partnerOfferings: [
          expect.objectContaining({ partnerOffering: mockEntities[0] }),
        ],
      }),
      {},
    );
  });

  it("should filter out partner offerings based on filter condition", async () => {
    const mockEntities = [
      {
        apiVersion: "aws.amazon.com/v1beta1",
        kind: "PartnerOffering",
        metadata: {
          name: "t1",
        },
        spec: {},
      },
      {
        apiVersion: "aws.amazon.com/v1beta1",
        kind: "PartnerOffering",
        metadata: {
          name: "t2",
        },
        spec: {},
      },
    ];

    (useEntityList as jest.Mock).mockReturnValue({
      entities: mockEntities,
      loading: false,
      error: null,
    });

    await renderInTestApp(
      <TestApiProvider apis={[[errorApiRef, {}]]}>
        <PartnerOfferingGroups
          groups={[{ title: "all", filter: (_) => true }]}
          partnerOfferingFilter={(e) => e.metadata.name === "t1"}
        />
      </TestApiProvider>,
    );

    expect(PartnerOfferingGroup).toHaveBeenCalledWith(
      expect.objectContaining({
        partnerOfferings: [
          expect.objectContaining({ partnerOffering: mockEntities[0] }),
        ],
      }),
      {},
    );
  });
});
