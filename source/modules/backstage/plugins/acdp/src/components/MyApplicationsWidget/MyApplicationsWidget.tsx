// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { InfoCard } from "@backstage/core-components";
import {
  MissingAnnotationEmptyState,
  useEntity,
} from "@backstage/plugin-catalog-react";

import { constants } from "backstage-plugin-acdp-common";

import { isDeploymentTargetAvailable } from "../../utils";
import { MyApplicationsWidgetContent } from "./MyApplicationsWidgetContent";

const queryClient = new QueryClient();

export const MyApplicationsWidget = () => {
  const { entity } = useEntity();

  return (
    <QueryClientProvider client={queryClient}>
      {!isDeploymentTargetAvailable(entity) ? (
        <MissingAnnotationEmptyState
          annotation={constants.ACDP_DEPLOYMENT_TARGET_ANNOTATION}
        />
      ) : (
        <InfoCard
          title="Service Catalog AppRegistry"
          subheader="Application Metrics"
        >
          <MyApplicationsWidgetContent />
        </InfoCard>
      )}
    </QueryClientProvider>
  );
};
