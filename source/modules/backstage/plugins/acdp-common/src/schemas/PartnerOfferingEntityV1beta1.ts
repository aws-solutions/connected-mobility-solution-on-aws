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

import {
  Entity,
  entityKindSchemaValidator,
  KindValidator,
} from "@backstage/catalog-model";
import schema from "./PartnerOffering.v1beta1.schema.json";

/**
 * Backstage catalog PartnerOffering kind Entity.
 * PartnerOfferings are used by the Partners page to display available Partner Offerings
 * @public
 */
export interface PartnerOfferingEntityV1beta1 extends Entity {
  /**
   * The apiVersion string of the TaskSpec.
   */
  apiVersion: "aws.amazon.com/v1beta1";
  /**
   * The kind of the entity
   */
  kind: "PartnerOffering";
  /**
   * The specification of the PartnerOffering Entity
   */
  spec: {
    /**
     * The type of software that the PartnerOffering is. For example service, service or application.
     */
    type: string;

    /**
     * The author of the PartnerOfferingEntity
     */
    author?: string;

    /**
     * The url to the author page for the PartnerOfferingEntity
     */
    authorPageUrl?: string;

    /**
     * The url to the source or marketplace page for the partner offering
     */
    url?: string;
  };
}

const validator = entityKindSchemaValidator(schema);

/**
 * Entity data validator for {@link PartnerOfferingEntityV1beta1}.
 *
 * @public
 */
export const partnerOfferingEntityV1beta1Validator: KindValidator = {
  async check(data: Entity) {
    return validator(data) === data;
  },
};

/**
 * Typeguard for filtering entities and ensuring v1beta3 entities
 * @public
 */
export const isPartnerOfferingEntityV1beta1 = (
  entity: Entity,
): entity is PartnerOfferingEntityV1beta1 =>
  entity.apiVersion === "aws.amazon.com/v1beta1" &&
  entity.kind === "PartnerOffering";
