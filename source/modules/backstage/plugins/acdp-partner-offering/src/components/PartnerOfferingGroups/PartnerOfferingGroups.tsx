// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

/*
 * Copyright 2022 The Backstage Authors
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
import React, { useCallback } from "react";

import { errorApiRef, IconComponent, useApi } from "@backstage/core-plugin-api";
import { useEntityList } from "@backstage/plugin-catalog-react";
import { Progress } from "@backstage/core-components";

import Typography from "@material-ui/core/Typography";

import {
  PartnerOfferingEntityV1beta1,
  isPartnerOfferingEntityV1beta1,
} from "backstage-plugin-acdp-common";

import { PartnerOfferingGroup } from "../PartnerOfferingGroup";
import { PartnerOfferingGroupFilter } from "../types";

/**
 * @alpha
 */
export interface PartnerOfferingGroupsProps {
  groups: PartnerOfferingGroupFilter[];
  partnerOfferingFilter?: (entity: PartnerOfferingEntityV1beta1) => boolean;
  PartnerOfferingCardComponent?: React.ComponentType<{
    partnerOffering: PartnerOfferingEntityV1beta1;
  }>;
  onPartnerOfferingSelected?: (
    partnerOffering: PartnerOfferingEntityV1beta1,
  ) => void;
  additionalLinksForEntity?: (
    partnerOffering: PartnerOfferingEntityV1beta1,
  ) => {
    icon: IconComponent;
    text: string;
    url: string;
  }[];
}

/**
 * @alpha
 */
export const PartnerOfferingGroups = (props: PartnerOfferingGroupsProps) => {
  const { loading, error, entities } = useEntityList();
  const {
    groups,
    partnerOfferingFilter: partnerOfferingFilter,
    PartnerOfferingCardComponent: PartnerOfferingCardComponent,
    onPartnerOfferingSelected: onPartnerOfferingSelected,
  } = props;
  const errorApi = useApi(errorApiRef);
  const onSelected = useCallback(
    (partnerOffering: PartnerOfferingEntityV1beta1) => {
      onPartnerOfferingSelected?.(partnerOffering);
    },
    [onPartnerOfferingSelected],
  );

  if (loading) {
    return <Progress />;
  }

  if (error) {
    errorApi.post(error);
    return null;
  }

  if (!entities || !entities.length) {
    return (
      <Typography variant="body2">
        No partner offerings found that match your filter.
      </Typography>
    );
  }

  return (
    <>
      {groups.map(({ title, filter }, index) => {
        const partnerOfferings = entities
          .filter(isPartnerOfferingEntityV1beta1)
          .filter((e) =>
            partnerOfferingFilter ? partnerOfferingFilter(e) : true,
          )
          .filter(filter)
          .map((partnerOffering) => {
            const additionalLinks =
              props.additionalLinksForEntity?.(partnerOffering) ?? [];

            return {
              partnerOffering,
              additionalLinks,
            };
          });

        return (
          <PartnerOfferingGroup
            key={`${title}-${index}`}
            partnerOfferings={partnerOfferings}
            title={title}
            components={{ CardComponent: PartnerOfferingCardComponent }}
            onSelected={onSelected}
          />
        );
      })}
    </>
  );
};
