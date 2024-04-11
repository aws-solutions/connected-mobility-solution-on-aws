// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0
/*
 * Copyright 2021 The Backstage Authors
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

jest.mock("./useTeardownConfirmDialogState");

import userEvent from "@testing-library/user-event";
import React from "react";
import { TeardownConfirmDialog } from "./TeardownConfirmDialog";
import { screen, waitFor } from "@testing-library/react";
import { renderInTestApp, TestApiProvider } from "@backstage/test-utils";
import * as state from "./useTeardownConfirmDialogState";

import { AlertApi, alertApiRef } from "@backstage/core-plugin-api";
import { stringifyEntityRef } from "@backstage/catalog-model";
import { entityRouteRef } from "@backstage/plugin-catalog-react";

describe("TeardownConfirmDialog", () => {
  const alertApi: AlertApi = {
    post() {
      return undefined;
    },
    alert$() {
      throw new Error("not implemented");
    },
  };

  beforeEach(() => {
    jest.spyOn(alertApi, "post").mockImplementation(() => {});
  });

  const entity = {
    apiVersion: "backstage.io/v1alpha1",
    kind: "Component",
    metadata: {
      name: "n",
      namespace: "ns",
      annotations: {},
    },
    spec: {},
  };

  const Wrapper = (props: { children?: React.ReactNode }) => (
    <TestApiProvider apis={[[alertApiRef, alertApi]]}>
      {props.children}
    </TestApiProvider>
  );

  const stateSpy = jest.spyOn(state, "useTeardownConfirmDialogState");

  afterEach(() => {
    jest.resetAllMocks();
  });

  it("can cancel", async () => {
    const onClose = jest.fn();
    stateSpy.mockImplementation(() => ({
      type: "teardown",
      entityRef: stringifyEntityRef(entity),
      teardownEntity: jest.fn(),
    }));

    await renderInTestApp(
      <Wrapper>
        <TeardownConfirmDialog
          open
          onClose={onClose}
          onConfirm={() => {}}
          entity={entity}
        />
      </Wrapper>,
      {
        mountedRoutes: {
          "/catalog/:namespace/:kind/:name/*": entityRouteRef,
        },
      },
    );

    await userEvent.click(screen.getByText("Cancel"));

    await waitFor(() => {
      expect(onClose).toHaveBeenCalled();
    });
  });

  it("handles the loading state", async () => {
    stateSpy.mockImplementation(() => ({ type: "loading" }));

    await renderInTestApp(
      <Wrapper>
        <TeardownConfirmDialog
          open
          onClose={() => {}}
          onConfirm={() => {}}
          entity={entity}
        />
      </Wrapper>,
      {
        mountedRoutes: {
          "/catalog/:namespace/:kind/:name/*": entityRouteRef,
        },
      },
    );

    await waitFor(() => {
      expect(screen.getByTestId("progress")).toBeInTheDocument();
    });
  });

  it("handles the error state", async () => {
    stateSpy.mockImplementation(() => ({
      type: "error",
      error: new TypeError("eek!"),
    }));

    await renderInTestApp(
      <Wrapper>
        <TeardownConfirmDialog
          open
          onClose={() => {}}
          onConfirm={() => {}}
          entity={entity}
        />
      </Wrapper>,
      {
        mountedRoutes: {
          "/catalog/:namespace/:kind/:name/*": entityRouteRef,
        },
      },
    );

    await waitFor(() => {
      expect(screen.getAllByText("eek!").length).toBeGreaterThan(0);
      expect(screen.getAllByText("TypeError").length).toBeGreaterThan(0);
    });
  });

  it("handles the unregister state, choosing to unregister", async () => {
    const teardownEntity = jest.fn();
    const onConfirm = jest.fn();

    stateSpy.mockImplementation(() => ({
      type: "teardown",
      entityRef: stringifyEntityRef(entity),
      teardownEntity,
    }));

    await renderInTestApp(
      <Wrapper>
        <TeardownConfirmDialog
          open
          onClose={() => {}}
          onConfirm={onConfirm}
          entity={entity}
        />
      </Wrapper>,
      {
        mountedRoutes: {
          "/catalog/:namespace/:kind/:name/*": entityRouteRef,
        },
      },
    );

    await waitFor(() => {
      expect(
        screen.getByText(
          /This action will run the teardown build for the following entity/,
        ),
      ).toBeInTheDocument();
      expect(screen.getByText(stringifyEntityRef(entity))).toBeInTheDocument();
    });

    await userEvent.click(screen.getByText("Confirm"));

    await waitFor(() => {
      expect(teardownEntity).toHaveBeenCalled();
      expect(onConfirm).toHaveBeenCalled();
    });
  });
});
