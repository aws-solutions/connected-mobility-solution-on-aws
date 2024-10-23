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
import React from "react";
import {
  Content,
  ContentHeader,
  ItemCardGrid,
} from "@backstage/core-components";
import { stringifyEntityRef } from "@backstage/catalog-model";
import {
  PartnerOfferingCardProps,
  PartnerOfferingCard,
} from "../PartnerOfferingCard";
import { IconComponent } from "@backstage/core-plugin-api";
import { PartnerOfferingEntityV1beta1 } from "backstage-plugin-acdp-common";

/**
 * The props for the {@link PartnerOfferingGroup} component.
 * @alpha
 */
export interface PartnerOfferingGroupProps {
  partnerOfferings: {
    partnerOffering: PartnerOfferingEntityV1beta1;
    additionalLinks?: {
      icon: IconComponent;
      text: string;
      url: string;
    }[];
  }[];
  onSelected: (partnerOffering: PartnerOfferingEntityV1beta1) => void;
  title: React.ReactNode;
  components?: {
    CardComponent?: React.ComponentType<PartnerOfferingCardProps>;
  };
}

/**
 * The `PartnerOfferingGroup` component is used to display a group of partner offerings with a title.
 * @alpha
 */
export const PartnerOfferingGroup = (props: PartnerOfferingGroupProps) => {
  const {
    partnerOfferings: partnerOfferings,
    title,
    components: { CardComponent } = {},
    onSelected,
  } = props;
  const titleComponent =
    typeof title === "string" ? <ContentHeader title={title} /> : title;

  if (partnerOfferings.length === 0) {
    return null;
  }

  const Card = CardComponent || PartnerOfferingCard;

  return (
    <Content>
      {titleComponent}
      <ItemCardGrid>
        {partnerOfferings.map(
          ({ partnerOffering: partnerOffering, additionalLinks }) => (
            <Card
              key={stringifyEntityRef(partnerOffering)}
              additionalLinks={additionalLinks}
              partnerOffering={partnerOffering}
              onSelected={onSelected}
            />
          ),
        )}
      </ItemCardGrid>
    </Content>
  );
};
