// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { IconButton } from "@material-ui/core";
import Cached from "@material-ui/icons/Cached";

import { InfoCard } from "@backstage/core-components";
import {
  useEntity,
  MissingAnnotationEmptyState,
} from "@backstage/plugin-catalog-react";

import { isDeploymentTargetAvailable } from "../../utils";
import { CodeBuildWidgetContent } from "./CodeBuildWidgetContent";

import { constants } from "backstage-plugin-acdp-common";

export interface AcdpBuildWidgetProps {
  buildHistoryLength?: number;
}

const queryClient = new QueryClient();

export const AcdpBuildWidget = (props: AcdpBuildWidgetProps) => {
  const { buildHistoryLength = 3 } = props;
  const { entity } = useEntity();

  return (
    <QueryClientProvider client={queryClient}>
      {!isDeploymentTargetAvailable(entity) ? (
        <MissingAnnotationEmptyState
          annotation={constants.ACDP_DEPLOYMENT_TARGET_ANNOTATION}
        />
      ) : (
        <InfoCard
          title="ACDP CodeBuild Project"
          action={
            <IconButton
              aria-label="Refresh"
              title="Refresh CodeBuild project build history"
              onClick={() =>
                queryClient.refetchQueries({
                  queryKey: ["getCodeBuildProjectBuilds"],
                })
              }
            >
              <Cached />
            </IconButton>
          }
        >
          <CodeBuildWidgetContent buildHistoryLength={buildHistoryLength} />
        </InfoCard>
      )}
    </QueryClientProvider>
  );
};
