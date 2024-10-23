// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

/*
 * Copyright 2020 The Backstage Authors
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

import { PartnerOfferingEntityV1beta1 } from "backstage-plugin-acdp-common";
import { PartnerOfferingEntitiesProcessor } from "./PartnerOfferingEntitiesProcessor";

const mockLocation = { type: "a", target: "b" };
const mockEntity: PartnerOfferingEntityV1beta1 = {
  apiVersion: "aws.amazon.com/v1beta1",
  kind: "PartnerOffering",
  metadata: { name: "n" },
  spec: {
    type: "service",
    author: "o",
  },
};

describe("ScaffolderEntitiesProcessor", () => {
  describe("validateEntityKind", () => {
    it("validates the entity kind", async () => {
      const processor = new PartnerOfferingEntitiesProcessor();

      await expect(processor.validateEntityKind(mockEntity)).resolves.toBe(
        true,
      );
      await expect(
        processor.validateEntityKind({
          ...mockEntity,
          apiVersion: "aws.amazon.com/v1beta0",
        }),
      ).resolves.toBe(false);
      await expect(
        processor.validateEntityKind({ ...mockEntity, kind: "Component" }),
      ).resolves.toBe(false);
    });
  });

  describe("postProcessEntity", () => {
    it("generates relations for component entities", async () => {
      const processor = new PartnerOfferingEntitiesProcessor();

      const emit = jest.fn();

      const entity = await processor.postProcessEntity(
        mockEntity,
        mockLocation,
        emit,
      );

      expect(entity).toBeDefined();
    });
  });
});
