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
import { DefaultStarredEntitiesApi } from "@backstage/plugin-catalog";
import {
  entityRouteRef,
  starredEntitiesApiRef,
} from "@backstage/plugin-catalog-react";
import {
  MockPermissionApi,
  MockStorageApi,
  renderInTestApp,
  TestApiProvider,
} from "@backstage/test-utils";
import { PartnerOfferingCard } from "./PartnerOfferingCard";

import { RELATION_OWNED_BY } from "@backstage/catalog-model";
import { fireEvent } from "@testing-library/react";
import { permissionApiRef } from "@backstage/plugin-permission-react";
import { PartnerOfferingEntityV1beta1 } from "backstage-plugin-acdp-common";

describe("PartnerOfferingCard", () => {
  it("should render the card title", async () => {
    const mockPartnerOffering: PartnerOfferingEntityV1beta1 = {
      apiVersion: "aws.amazon.com/v1beta1",
      kind: "PartnerOffering",
      metadata: { name: "bob" },
      spec: {
        type: "service",
      },
    };

    const { getByText } = await renderInTestApp(
      <TestApiProvider
        apis={[
          [
            starredEntitiesApiRef,
            new DefaultStarredEntitiesApi({
              storageApi: MockStorageApi.create(),
            }),
          ],
          [permissionApiRef, new MockPermissionApi()],
        ]}
      >
        <PartnerOfferingCard partnerOffering={mockPartnerOffering} />
      </TestApiProvider>,
    );

    expect(getByText("bob")).toBeInTheDocument();
  });

  it("should render the description as markdown", async () => {
    const mockPartnerOffering: PartnerOfferingEntityV1beta1 = {
      apiVersion: "aws.amazon.com/v1beta1",
      kind: "PartnerOffering",
      metadata: { name: "bob", description: "hello **test**" },
      spec: {
        type: "service",
      },
    };

    const { getByText, getByTestId } = await renderInTestApp(
      <TestApiProvider
        apis={[
          [
            starredEntitiesApiRef,
            new DefaultStarredEntitiesApi({
              storageApi: MockStorageApi.create(),
            }),
          ],
          [permissionApiRef, new MockPermissionApi()],
        ]}
      >
        <PartnerOfferingCard partnerOffering={mockPartnerOffering} />
      </TestApiProvider>,
    );

    const description = getByText("hello");
    expect(description.querySelector("strong")).toBeInTheDocument();
    expect(getByTestId("partnerOffering-card-separator")).toBeInTheDocument();
  });

  it("should render no description if none is provided through the partner offering", async () => {
    const mockPartnerOffering: PartnerOfferingEntityV1beta1 = {
      apiVersion: "aws.amazon.com/v1beta1",
      kind: "PartnerOffering",
      metadata: { name: "bob" },
      spec: {
        type: "service",
      },
    };

    const { getByText } = await renderInTestApp(
      <TestApiProvider
        apis={[
          [
            starredEntitiesApiRef,
            new DefaultStarredEntitiesApi({
              storageApi: MockStorageApi.create(),
            }),
          ],
          [permissionApiRef, new MockPermissionApi()],
        ]}
      >
        <PartnerOfferingCard partnerOffering={mockPartnerOffering} />
      </TestApiProvider>,
    );

    expect(getByText("No description")).toBeInTheDocument();
  });

  it("should not render extra separators when tags or links are not present", async () => {
    const mockPartnerOffering: PartnerOfferingEntityV1beta1 = {
      apiVersion: "aws.amazon.com/v1beta1",
      kind: "PartnerOffering",
      metadata: { name: "bob" },
      spec: {
        type: "service",
      },
    };

    const { queryByTestId } = await renderInTestApp(
      <TestApiProvider
        apis={[
          [
            starredEntitiesApiRef,
            new DefaultStarredEntitiesApi({
              storageApi: MockStorageApi.create(),
            }),
          ],
          [permissionApiRef, new MockPermissionApi()],
        ]}
      >
        <PartnerOfferingCard partnerOffering={mockPartnerOffering} />
      </TestApiProvider>,
    );

    expect(queryByTestId("partnerOffering-card-separator")).toBeInTheDocument();
    expect(
      queryByTestId("partnerOffering-card-separator--tags"),
    ).not.toBeInTheDocument();
    expect(
      queryByTestId("partnerOffering-card-separator--links"),
    ).not.toBeInTheDocument();
  });

  it("should render the tags", async () => {
    const mockPartnerOffering: PartnerOfferingEntityV1beta1 = {
      apiVersion: "aws.amazon.com/v1beta1",
      kind: "PartnerOffering",
      metadata: { name: "bob", tags: ["cpp", "react"] },
      spec: {
        type: "service",
      },
    };

    const { getByText, queryByTestId } = await renderInTestApp(
      <TestApiProvider
        apis={[
          [
            starredEntitiesApiRef,
            new DefaultStarredEntitiesApi({
              storageApi: MockStorageApi.create(),
            }),
          ],
          [permissionApiRef, new MockPermissionApi()],
        ]}
      >
        <PartnerOfferingCard partnerOffering={mockPartnerOffering} />
      </TestApiProvider>,
    );

    for (const tag of mockPartnerOffering.metadata.tags!) {
      expect(getByText(tag)).toBeInTheDocument();
    }
    expect(
      queryByTestId("partnerOffering-card-separator"),
    ).not.toBeInTheDocument();
    expect(
      queryByTestId("partnerOffering-card-separator--tags"),
    ).toBeInTheDocument();
  });

  it("should not render links section when empty links are defined", async () => {
    const mockPartnerOffering: PartnerOfferingEntityV1beta1 = {
      apiVersion: "aws.amazon.com/v1beta1",
      kind: "PartnerOffering",
      metadata: { name: "bob", tags: [], links: [] },
      spec: {
        type: "service",
      },
      relations: [
        {
          targetRef: "group:default/my-test-user",
          type: RELATION_OWNED_BY,
        },
      ],
    };

    const { queryByTestId, queryByText } = await renderInTestApp(
      <TestApiProvider
        apis={[
          [
            starredEntitiesApiRef,
            new DefaultStarredEntitiesApi({
              storageApi: MockStorageApi.create(),
            }),
          ],
          [permissionApiRef, new MockPermissionApi()],
        ]}
      >
        <PartnerOfferingCard partnerOffering={mockPartnerOffering} />
      </TestApiProvider>,
      {
        mountedRoutes: {
          "/catalog/:kind/:namespace/:name": entityRouteRef,
        },
      },
    );

    expect(queryByTestId("partnerOffering-card-separator")).toBeInTheDocument();
    expect(
      queryByTestId("partnerOffering-card-separator--links"),
    ).not.toBeInTheDocument();
    expect(queryByText("0")).not.toBeInTheDocument();
  });

  it("should not render links section when empty additional links are defined", async () => {
    const mockPartnerOffering: PartnerOfferingEntityV1beta1 = {
      apiVersion: "aws.amazon.com/v1beta1",
      kind: "PartnerOffering",
      metadata: { name: "bob", tags: [], links: [] },
      spec: {
        type: "service",
      },
      relations: [
        {
          targetRef: "group:default/my-test-user",
          type: RELATION_OWNED_BY,
        },
      ],
    };

    const { queryByTestId, queryByText } = await renderInTestApp(
      <TestApiProvider
        apis={[
          [
            starredEntitiesApiRef,
            new DefaultStarredEntitiesApi({
              storageApi: MockStorageApi.create(),
            }),
          ],
          [permissionApiRef, new MockPermissionApi()],
        ]}
      >
        <PartnerOfferingCard
          partnerOffering={mockPartnerOffering}
          additionalLinks={[]}
        />
      </TestApiProvider>,
      {
        mountedRoutes: {
          "/catalog/:kind/:namespace/:name": entityRouteRef,
        },
      },
    );

    expect(queryByTestId("partnerOffering-card-separator")).toBeInTheDocument();
    expect(
      queryByTestId("partnerOffering-card-separator--links"),
    ).not.toBeInTheDocument();
    expect(queryByText("0")).not.toBeInTheDocument();
  });

  it("should render links section when links are defined", async () => {
    const mockPartnerOffering: PartnerOfferingEntityV1beta1 = {
      apiVersion: "aws.amazon.com/v1beta1",
      kind: "PartnerOffering",
      metadata: {
        name: "bob",
        tags: [],
        links: [{ url: "/some/url", title: "Learn More" }],
      },
      spec: {
        type: "service",
      },
      relations: [
        {
          targetRef: "group:default/my-test-user",
          type: RELATION_OWNED_BY,
        },
      ],
    };

    const { queryByTestId, getByRole } = await renderInTestApp(
      <TestApiProvider
        apis={[
          [
            starredEntitiesApiRef,
            new DefaultStarredEntitiesApi({
              storageApi: MockStorageApi.create(),
            }),
          ],
          [permissionApiRef, new MockPermissionApi()],
        ]}
      >
        <PartnerOfferingCard
          partnerOffering={mockPartnerOffering}
          additionalLinks={[]}
        />
      </TestApiProvider>,
      {
        mountedRoutes: {
          "/catalog/:kind/:namespace/:name": entityRouteRef,
        },
      },
    );

    expect(
      queryByTestId("partnerOffering-card-separator"),
    ).not.toBeInTheDocument();
    expect(
      queryByTestId("partnerOffering-card-separator--links"),
    ).toBeInTheDocument();
    expect(getByRole("link", { name: "Learn More" })).toBeInTheDocument();
  });

  it("should call the onSelected handler when clicking the choose button", async () => {
    const mockPartnerOffering: PartnerOfferingEntityV1beta1 = {
      apiVersion: "aws.amazon.com/v1beta1",
      kind: "PartnerOffering",
      metadata: { name: "bob", tags: ["cpp", "react"] },
      spec: {
        type: "service",
      },
    };
    const mockOnSelected = jest.fn();

    const { getByRole } = await renderInTestApp(
      <TestApiProvider
        apis={[
          [
            starredEntitiesApiRef,
            new DefaultStarredEntitiesApi({
              storageApi: MockStorageApi.create(),
            }),
          ],
          [permissionApiRef, new MockPermissionApi()],
        ]}
      >
        <PartnerOfferingCard
          partnerOffering={mockPartnerOffering}
          onSelected={mockOnSelected}
        />
      </TestApiProvider>,
      {
        mountedRoutes: {
          "/catalog/:kind/:namespace/:name": entityRouteRef,
        },
      },
    );

    expect(getByRole("button", { name: "Choose" })).toBeInTheDocument();

    fireEvent.click(getByRole("button", { name: "Choose" }));

    expect(mockOnSelected).toHaveBeenCalledWith(mockPartnerOffering);
  });
});
