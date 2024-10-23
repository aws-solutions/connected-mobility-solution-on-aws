// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React from "react";

import { AnyApiRef } from "@backstage/core-plugin-api";
import { EntityProvider } from "@backstage/plugin-catalog-react";
import { wrapInTestApp, TestApiProvider } from "@backstage/test-utils";
import { render } from "@testing-library/react";

import { MyApplicationsWidget } from "./MyApplicationsWidget";

import { acdpMetricsApiRef } from "../../api";
import { mockMetricsEntity, MockAcdpMetricsApi } from "../../mocks";

const apis: [AnyApiRef, Partial<unknown>][] = [
  [acdpMetricsApiRef, new MockAcdpMetricsApi()],
];

describe("MyApplicationsWidget", () => {
  it("should display widget with correct title", async () => {
    const rendered = render(
      wrapInTestApp(
        <TestApiProvider apis={apis}>
          <EntityProvider entity={mockMetricsEntity}>
            <MyApplicationsWidget />
          </EntityProvider>
        </TestApiProvider>,
      ),
    );
    expect(
      await rendered.findByText("Service Catalog AppRegistry"),
    ).toBeInTheDocument();
  });
});
