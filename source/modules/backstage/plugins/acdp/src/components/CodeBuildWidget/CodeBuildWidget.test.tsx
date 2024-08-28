// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

/**
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * Licensed under the Apache License, Version 2.0 (the "License").
 * You may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *     http://www.apache.org/licenses/LICENSE-2.0
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import { AnyApiRef } from "@backstage/core-plugin-api";
import { EntityProvider } from "@backstage/plugin-catalog-react";
import {
  setupRequestMockHandlers,
  TestApiProvider,
  wrapInTestApp,
} from "@backstage/test-utils";
import { act, render, waitFor } from "@testing-library/react";
import { setupServer } from "msw/node";
import React from "react";
import { acdpBuildApiRef } from "../../api";
import {
  mockCodeBuildEntity,
  MockCodeBuildService,
} from "../../mocks/mocksCodeBuild";
import { AcdpBuildWidget } from "./CodeBuildWidget";

const apis: [AnyApiRef, Partial<unknown>][] = [
  [acdpBuildApiRef, new MockCodeBuildService()],
];

describe("AcdpBuildWidget", () => {
  const worker = setupServer();
  setupRequestMockHandlers(worker);

  it("should display widget when ARN is present", async () => {
    const rendered = render(
      wrapInTestApp(
        <TestApiProvider apis={apis}>
          <EntityProvider entity={mockCodeBuildEntity}>
            <AcdpBuildWidget />
          </EntityProvider>
        </TestApiProvider>,
      ),
    );
    expect(await rendered.findByText("test-project")).toBeInTheDocument();
    expect(await rendered.findAllByText("Succeeded")).toHaveLength(3);
  });

  it("should load and refresh on update button click", async () => {
    const rendered = render(
      wrapInTestApp(
        <TestApiProvider apis={apis}>
          <EntityProvider entity={mockCodeBuildEntity}>
            <AcdpBuildWidget />
          </EntityProvider>
        </TestApiProvider>,
      ),
    );
    expect(await rendered.findByText("test-project")).toBeInTheDocument();
    (await rendered.findByText("Update")).click();
    await waitFor(() => {
      expect(rendered.getByRole("progressbar")).toBeInTheDocument();
    });
    await waitFor(() => {
      expect(rendered.queryByRole("progressbar")).not.toBeInTheDocument();
    });
    expect(await rendered.findAllByText("Succeeded")).toHaveLength(3);
  });

  it("should load and refresh on teardown button click", async () => {
    const rendered = render(
      wrapInTestApp(
        <TestApiProvider apis={apis}>
          <EntityProvider entity={mockCodeBuildEntity}>
            <AcdpBuildWidget />
          </EntityProvider>
        </TestApiProvider>,
      ),
    );
    expect(await rendered.findByText("test-project")).toBeInTheDocument();
    await act(async () => {
      (await rendered.findByText("Teardown")).click();
    });
    await waitFor(async () => {
      expect(await rendered.findByText("Confirm")).toBeInTheDocument();
    });
    await act(async () => {
      (await rendered.findByText("Confirm")).click();
    });

    await waitFor(async () => {
      expect(rendered.getByRole("progressbar")).toBeInTheDocument();
    });
    await waitFor(() => {
      expect(rendered.queryByRole("progressbar")).not.toBeInTheDocument();
    });
    expect(await rendered.findAllByText("Succeeded")).toHaveLength(3);
  });
});
