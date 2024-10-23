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

import { useCallback } from "react";
import useAsync from "react-use/lib/useAsync";

import { Entity, stringifyEntityRef } from "@backstage/catalog-model";

/**
 * Each distinct state that the dialog can be in at any given time.
 */
export type UseTeardownConfirmDialogState =
  | {
      type: "loading";
    }
  | {
      type: "error";
      error: Error;
    }
  | {
      type: "teardown";
      entityRef: string;
      teardownEntity: () => boolean;
    };

/**
 * Houses the main logic for unregistering entities and their locations.
 */
export function useTeardownConfirmDialogState(
  entity: Entity,
): UseTeardownConfirmDialogState {
  const entityRef = stringifyEntityRef(entity);

  // Load the prerequisite data: what entities that are colocated with us, and what location that spawned us
  const prerequisites = useAsync(async () => {
    // future: fetch CFN template status here.
  }, [entity]);

  const teardownEntity = useCallback(function teardownEntityConfirm() {
    return true;
  }, []);

  // Return early if prerequisites still loading or failing
  const { loading, error } = prerequisites;
  if (loading) {
    return { type: "loading" };
  } else if (error) {
    return { type: "error", error };
  }

  return {
    type: "teardown",
    entityRef: entityRef,
    teardownEntity: teardownEntity,
  };
}
