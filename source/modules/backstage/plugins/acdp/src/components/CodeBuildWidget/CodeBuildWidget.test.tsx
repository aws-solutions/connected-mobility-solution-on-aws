// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { AnyApiRef } from "@backstage/core-plugin-api";
import { EntityProvider } from "@backstage/plugin-catalog-react";
import {
  registerMswTestHooks,
  TestApiProvider,
  wrapInTestApp,
} from "@backstage/test-utils";

import { act, render, waitFor } from "@testing-library/react";
import { setupServer } from "msw/node";

import { acdpBuildApiRef } from "../../api";
import { mockCodeBuildEntity, MockAcdpBuildApi } from "../../mocks";
import { AcdpBuildWidget } from "./CodeBuildWidget";

const apis: [AnyApiRef, Partial<unknown>][] = [
  [acdpBuildApiRef, new MockAcdpBuildApi()],
];

describe("AcdpBuildWidget", () => {
  const worker = setupServer();
  registerMswTestHooks(worker);

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
