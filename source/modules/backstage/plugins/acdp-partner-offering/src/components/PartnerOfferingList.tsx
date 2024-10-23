// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {
  Page,
  Header,
  Content,
  ContentHeader,
} from "@backstage/core-components";
import {
  CatalogFilterLayout,
  EntityKindPicker,
  EntityListProvider,
  EntitySearchBar,
  EntityTagPicker,
  UserListPicker,
} from "@backstage/plugin-catalog-react";
import { PartnerOfferingCategoryPicker } from "./PartnerOfferingCategoryPicker";
import { PartnerOfferingGroups } from "./PartnerOfferingGroups";
import { PartnerOfferingGroupFilter } from "./types";
import { PartnerOfferingEntityV1beta1 } from "backstage-plugin-acdp-common";
import React from "react";

export type PartnerOfferingListPageProps = {
  PartnerOfferingCardComponent?: React.ComponentType<{
    partnerOffering: PartnerOfferingEntityV1beta1;
  }>;
  groups?: PartnerOfferingGroupFilter[];
  partnerOfferingFilter?: (entity: PartnerOfferingEntityV1beta1) => boolean;
  contextMenu?: {
    editor?: boolean;
    actions?: boolean;
    tasks?: boolean;
  };
  headerOptions?: {
    pageTitleOverride?: string;
    title?: string;
    subtitle?: string;
  };
};

const defaultGroup: PartnerOfferingGroupFilter = {
  title: "Partner Offerings",
  filter: () => true,
};

const createGroupsWithOther = (
  groups: PartnerOfferingGroupFilter[],
): PartnerOfferingGroupFilter[] => [
  ...groups,
  {
    title: "Other Partner Offerings",
    filter: (e) => ![...groups].some(({ filter }) => filter(e)),
  },
];

export const PartnerOfferingListPage = (
  props: PartnerOfferingListPageProps,
) => {
  const {
    PartnerOfferingCardComponent: PartnerOfferingCardComponent,
    groups: givenGroups = [],
    partnerOfferingFilter: partnerOfferingFilter,
  } = props;

  const groups = givenGroups.length
    ? createGroupsWithOther(givenGroups)
    : [defaultGroup];

  const onPartnerOfferingSelected = (
    partnerOffering: PartnerOfferingEntityV1beta1,
  ) => {
    window.open(partnerOffering.spec.url, "_blank");
  };

  return (
    <EntityListProvider>
      <Page themeId="home">
        <Header
          title="Browse Partner Offerings"
          subtitle="A curated list of partner offerings that can be deployed alongside CMS on AWS"
          pageTitleOverride="Partner Offerings"
        />
        <Content>
          <ContentHeader title="Available Partner Offerings" />
          <CatalogFilterLayout>
            <CatalogFilterLayout.Filters>
              <EntitySearchBar />
              <EntityKindPicker initialFilter="PartnerOffering" hidden />
              <UserListPicker
                initialFilter="all"
                availableFilters={["all", "starred"]}
              />
              <PartnerOfferingCategoryPicker />
              <EntityTagPicker />
            </CatalogFilterLayout.Filters>
            <CatalogFilterLayout.Content>
              <PartnerOfferingGroups
                groups={groups}
                partnerOfferingFilter={partnerOfferingFilter}
                PartnerOfferingCardComponent={PartnerOfferingCardComponent}
                onPartnerOfferingSelected={onPartnerOfferingSelected}
                // additionalLinksForEntity={additionalLinksForEntity}
              />
            </CatalogFilterLayout.Content>
          </CatalogFilterLayout>
        </Content>
      </Page>
    </EntityListProvider>
  );
};
