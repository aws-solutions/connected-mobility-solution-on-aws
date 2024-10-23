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

import { entityKindSchemaValidator } from "@backstage/catalog-model";
import type { PartnerOfferingEntityV1beta1 } from "./PartnerOfferingEntityV1beta1";
import schema from "./PartnerOffering.v1beta1.schema.json";

const validator = entityKindSchemaValidator(schema);

describe("partnerOfferingEntityV1beta1Validator", () => {
  let entity: PartnerOfferingEntityV1beta1;

  beforeEach(() => {
    entity = {
      apiVersion: "aws.amazon.com/v1beta1",
      kind: "PartnerOffering",
      metadata: {
        name: "test",
      },
      spec: {
        type: "website",
        author: "team-b",
      },
    };
  });

  it("happy path: accepts valid data", async () => {
    expect(validator(entity)).toBe(entity);
  });

  it("ignores unknown apiVersion", async () => {
    (entity as any).apiVersion = "aws.amazon.com/v1beta0";
    expect(validator(entity)).toBe(false);
  });

  it("ignores unknown kind", async () => {
    (entity as any).kind = "Wizard";
    expect(validator(entity)).toBe(false);
  });

  it("rejects missing type", async () => {
    delete (entity as any).spec.type;
    expect(() => validator(entity)).toThrow(/type/);
  });

  it("accepts any other type", async () => {
    (entity as any).spec.type = "hallo";
    expect(validator(entity)).toBe(entity);
  });

  it("accepts missing parameters", async () => {
    delete (entity as any).spec.parameters;
    expect(validator(entity)).toBe(entity);
  });

  it("accepts missing outputs", async () => {
    delete (entity as any).spec.outputs;
    expect(validator(entity)).toBe(entity);
  });

  it("rejects empty type", async () => {
    (entity as any).spec.type = "";
    expect(() => validator(entity)).toThrow(/type/);
  });

  it("accepts missing author", async () => {
    delete (entity as any).spec.author;
    expect(validator(entity)).toBe(entity);
  });

  it("rejects empty author", async () => {
    (entity as any).spec.author = "";
    expect(() => validator(entity)).toThrow(/author/);
  });

  it("rejects wrong type author", async () => {
    (entity as any).spec.author = 5;
    expect(() => validator(entity)).toThrow(/author/);
  });
});
