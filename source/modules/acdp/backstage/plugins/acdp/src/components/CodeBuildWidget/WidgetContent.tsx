// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React, { useState } from "react";
import { Button, LinearProgress } from "@material-ui/core";
import {
  useMutation,
  useIsMutating,
  useQueryClient,
  useQuery,
} from "@tanstack/react-query";

import { useEntity } from "@backstage/plugin-catalog-react";
import { useApi } from "@backstage/core-plugin-api";

import { MostRecentBuild } from "./MostRecentBuild";
import { BuildHistoryTable } from "./BuildHistoryTable";
import { StartBuildInput, acdpBuildApiRef } from "../../api";
import { ResponseErrorPanel } from "@backstage/core-components";
import { stringifyEntityRef } from "@backstage/catalog-model";
import { parseCodeBuildArn } from "../../utils";
import { TeardownConfirmDialog } from "./TeardownConfirmDialog/TeardownConfirmDialog";
import { AcdpBuildAction } from "backstage-plugin-acdp-common";

interface WidgetContentProps {
  buildHistoryLength: number;
}

export const WidgetContent = (props: WidgetContentProps) => {
  const { buildHistoryLength } = props;
  const api = useApi(acdpBuildApiRef);
  const { entity } = useEntity();
  const entityRef = stringifyEntityRef(entity);
  const queryClient = useQueryClient();

  const getCodeBuildProjectBuildsQuery = useQuery({
    queryKey: ["getCodeBuildProjectBuilds"],
    queryFn: async () => {
      const project = await api.getProject({ entityRef: entityRef });

      if (!project || !project.arn) {
        throw new Error("No CodeBuild Project Found");
      }

      const builds = await api.listBuilds({ entityRef: entityRef });
      const { accountId, region } = parseCodeBuildArn(project.arn!);

      return { project, builds, accountId, region };
    },
  });

  const startUpdateBuildMutation = useMutation({
    mutationKey: ["startCodeBuild"],
    mutationFn: (input: StartBuildInput) => api.startBuild(input),
    onSuccess: () =>
      queryClient.invalidateQueries({
        queryKey: ["getCodeBuildProjectBuilds"],
      }),
  });

  const startTeardownBuildMutation = useMutation({
    mutationKey: ["startCodeBuild"],
    mutationFn: (input: StartBuildInput) => api.startBuild(input),
    onSuccess: () =>
      queryClient.invalidateQueries({
        queryKey: ["getCodeBuildProjectBuilds"],
      }),
  });

  const startCodeBuildMutationCount = useIsMutating({
    mutationKey: ["startCodeBuild"],
  });

  const [confirmationDialogOpen, setConfirmationDialogOpen] = useState(false);

  const cleanUpAfterTeardown = async () => {
    setConfirmationDialogOpen(false);
    startTeardownBuildMutation.mutate({
      entityRef: entityRef,
      action: AcdpBuildAction.TEARDOWN,
    });
    //todo: on success, unregister the entity?
  };

  return (
    <>
      {(getCodeBuildProjectBuildsQuery.isFetching ||
        startCodeBuildMutationCount > 0) && <LinearProgress />}
      {getCodeBuildProjectBuildsQuery.isSuccess &&
        getCodeBuildProjectBuildsQuery.data?.project &&
        getCodeBuildProjectBuildsQuery.data.builds && (
          <>
            <MostRecentBuild
              project={getCodeBuildProjectBuildsQuery.data.project}
              builds={getCodeBuildProjectBuildsQuery.data.builds}
            />
            {buildHistoryLength > 0 && (
              <BuildHistoryTable
                region={getCodeBuildProjectBuildsQuery.data.region}
                accountId={getCodeBuildProjectBuildsQuery.data.accountId}
                project={getCodeBuildProjectBuildsQuery.data.project.name}
                builds={getCodeBuildProjectBuildsQuery.data.builds}
                buildHistoryLength={buildHistoryLength}
              />
            )}
            <br />
            <Button
              color="primary"
              className="button-theme header-button"
              onClick={() => {
                startUpdateBuildMutation.mutate({
                  entityRef: entityRef,
                  action: AcdpBuildAction.UPDATE,
                });
              }}
              disabled={
                startCodeBuildMutationCount > 0 ||
                getCodeBuildProjectBuildsQuery.data.builds.some(
                  (build) => build.buildStatus === "IN_PROGRESS",
                )
              }
            >
              Update
            </Button>
            <Button
              color="secondary"
              className="button-theme header-button"
              onClick={() => {
                setConfirmationDialogOpen(true);
              }}
              disabled={
                startCodeBuildMutationCount > 0 ||
                getCodeBuildProjectBuildsQuery.data.builds.some(
                  (build) => build.buildStatus === "IN_PROGRESS",
                )
              }
            >
              Teardown
            </Button>
          </>
        )}
      {getCodeBuildProjectBuildsQuery.isError && (
        <ResponseErrorPanel
          error={getCodeBuildProjectBuildsQuery.error as Error}
        />
      )}
      <TeardownConfirmDialog
        open={confirmationDialogOpen}
        entity={entity}
        onConfirm={cleanUpAfterTeardown}
        onClose={() => setConfirmationDialogOpen(false)}
      />
    </>
  );
};
