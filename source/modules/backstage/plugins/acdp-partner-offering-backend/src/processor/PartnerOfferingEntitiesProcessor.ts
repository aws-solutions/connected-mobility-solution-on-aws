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

import { Entity } from "@backstage/catalog-model";
import {
  CatalogProcessor,
  CatalogProcessorEmit,
} from "@backstage/plugin-catalog-node";
import { LocationSpec } from "@backstage/plugin-catalog-common";
import { partnerOfferingEntityV1beta1Validator } from "backstage-plugin-acdp-common";

/**
 * Adds support for partner offering specific entity kinds to the catalog.
 *
 * @public
 */
export class PartnerOfferingEntitiesProcessor implements CatalogProcessor {
  getProcessorName(): string {
    return "PartnerOfferingEntitiesProcessor";
  }

  private readonly validators = [partnerOfferingEntityV1beta1Validator];

  async validateEntityKind(entity: Entity): Promise<boolean> {
    for (const validator of this.validators) {
      if (await validator.check(entity)) {
        return true;
      }
    }

    return false;
  }

  async postProcessEntity(
    entity: Entity,
    _location: LocationSpec,
    _emit: CatalogProcessorEmit,
  ): Promise<Entity> {
    return entity;
  }
}
