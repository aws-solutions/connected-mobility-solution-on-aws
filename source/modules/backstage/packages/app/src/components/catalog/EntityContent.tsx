// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React from "react";
import { Grid } from "@material-ui/core";
import {
  EntityConsumedApisCard,
  EntityProvidedApisCard,
} from "@backstage/plugin-api-docs";
import {
  EntityAboutCard,
  EntityDependsOnComponentsCard,
  EntityDependsOnResourcesCard,
  EntityHasSubcomponentsCard,
  EntityLinksCard,
  EntitySwitch,
  EntityOrphanWarning,
  EntityProcessingErrorsPanel,
  hasCatalogProcessingErrors,
  isOrphan,
} from "@backstage/plugin-catalog";
import { EntityTechdocsContent } from "@backstage/plugin-techdocs";
import { EntityCatalogGraphCard } from "@backstage/plugin-catalog-graph";

import { TechDocsAddons } from "@backstage/plugin-techdocs-react";
import { ReportIssue } from "@backstage/plugin-techdocs-module-addons-contrib";

import { EntityAcdpBuildProjectOverviewCard } from "backstage-plugin-acdp";

export const entityWarningContent = (
  <>
    <EntitySwitch>
      <EntitySwitch.Case if={isOrphan}>
        <Grid item xs={12}>
          <EntityOrphanWarning />
        </Grid>
      </EntitySwitch.Case>
    </EntitySwitch>

    <EntitySwitch>
      <EntitySwitch.Case if={hasCatalogProcessingErrors}>
        <Grid item xs={12}>
          <EntityProcessingErrorsPanel />
        </Grid>
      </EntitySwitch.Case>
    </EntitySwitch>
  </>
);

export const overviewContent = (
  <Grid container spacing={3} alignItems="stretch">
    {entityWarningContent}
    <Grid item md={6}>
      <EntityAboutCard variant="gridItem" />
    </Grid>
    <Grid item md={6} xs={12}>
      <EntityCatalogGraphCard variant="gridItem" height={400} />
    </Grid>
    <Grid item md={4} xs={12}>
      <EntityLinksCard />
    </Grid>
    <Grid item md={8} xs={12}>
      <EntityHasSubcomponentsCard variant="gridItem" />
    </Grid>
  </Grid>
);

export const cicdContent = (
  <Grid item sm={6}>
    <EntityAcdpBuildProjectOverviewCard />
  </Grid>
);

export const apiContent = (
  <Grid container spacing={3} alignItems="stretch">
    <Grid item md={6}>
      <EntityProvidedApisCard />
    </Grid>
    <Grid item md={6}>
      <EntityConsumedApisCard />
    </Grid>
  </Grid>
);

export const dependenciesContent = (
  <Grid container spacing={3} alignItems="stretch">
    <Grid item md={6}>
      <EntityDependsOnComponentsCard variant="gridItem" />
    </Grid>
    <Grid item md={6}>
      <EntityDependsOnResourcesCard variant="gridItem" />
    </Grid>
  </Grid>
);

export const techdocsContent = (
  <EntityTechdocsContent>
    <TechDocsAddons>
      <ReportIssue />
    </TechDocsAddons>
  </EntityTechdocsContent>
);
