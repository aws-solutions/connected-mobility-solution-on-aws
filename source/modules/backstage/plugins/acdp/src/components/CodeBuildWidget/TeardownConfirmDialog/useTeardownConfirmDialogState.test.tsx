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

import { Entity, stringifyEntityRef } from "@backstage/catalog-model";
import { renderHook, waitFor } from "@testing-library/react";
import { useTeardownConfirmDialogState } from "./useTeardownConfirmDialogState";

describe("useTeardownConfirmDialogState", () => {
  let entity: Entity;

  beforeEach(() => {
    jest.resetAllMocks();

    entity = {
      apiVersion: "backstage.io/v1alpha1",
      kind: "Component",
      metadata: {
        name: "n",
        namespace: "ns",
        annotations: {},
      },
      spec: {},
    };
  });

  it("goes through the confirm path", async () => {
    const rendered = renderHook(
      () => useTeardownConfirmDialogState(entity),
      {},
    );

    expect(rendered.result.current).toEqual({ type: "loading" });

    await waitFor(() => {
      expect(rendered.result.current).toEqual({
        type: "teardown",
        entityRef: stringifyEntityRef(entity),
        teardownEntity: expect.any(Function),
      });
    });
  });
});
