// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React from "react";
import { Box, Grid, Link } from "@material-ui/core";

import { formatDistanceStrict } from "date-fns";

import { AboutField } from "../AboutField";
import { BuildStatus } from "../BuildStatus";

import { parseCodeBuildArn } from "../../utils";
import {
  AcdpBuildProject,
  AcdpBuildProjectBuild,
} from "backstage-plugin-acdp-common";

const projectMostRecentBuildStatus = (builds: AcdpBuildProjectBuild[]) => {
  return builds.length > 0 ? (
    <BuildStatus status={builds[0].buildStatus} />
  ) : (
    <></>
  );
};

const projectMostRecentBuildExecuted = (builds: AcdpBuildProjectBuild[]) => {
  const build = builds.find((b) => b.startTime);
  return build
    ? `${formatDistanceStrict(new Date(build.startTime!), new Date())} ago`
    : "";
};

const projectMostRecentBuildDuration = (builds: AcdpBuildProjectBuild[]) => {
  const build = builds.find((b) => b.startTime && b.endTime);
  return build
    ? formatDistanceStrict(new Date(build.startTime!), new Date(build.endTime!))
    : "";
};

interface MostRecentBuildProps {
  project: AcdpBuildProject;
  builds: AcdpBuildProjectBuild[];
}

export const MostRecentBuild = (props: MostRecentBuildProps) => {
  const { project, builds } = props;
  const { accountId, region } = parseCodeBuildArn(project.arn!);

  return (
    <Box sx={{ m: 2 }}>
      <Grid container>
        <AboutField label="Project Name" gridSizes={{ md: 12 }}>
          <Link
            href={`https://${region}.console.aws.amazon.com/codesuite/codebuild/${accountId}/projects/${project.name}/?region=${region}`}
            target="_blank"
          >
            {project.name}
          </Link>
        </AboutField>
        <AboutField
          label="Most recent build"
          gridSizes={{ xs: 12, sm: 6, lg: 4 }}
        >
          {projectMostRecentBuildStatus(builds)}
        </AboutField>
        <AboutField label="Last executed" gridSizes={{ xs: 12, sm: 6, lg: 4 }}>
          {projectMostRecentBuildExecuted(builds)}
        </AboutField>
        <AboutField label="Duration" gridSizes={{ xs: 12, sm: 6, lg: 4 }}>
          {projectMostRecentBuildDuration(builds)}
        </AboutField>
      </Grid>
    </Box>
  );
};
