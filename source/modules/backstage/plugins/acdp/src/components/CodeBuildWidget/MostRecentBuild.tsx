// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { formatDistanceStrict } from "date-fns";

import { Box, Grid, Link } from "@material-ui/core";

import {
  AcdpBuildProject,
  AcdpBuildProjectBuild,
} from "backstage-plugin-acdp-common";

import { parseCodeBuildArn } from "../../utils";
import { AboutField } from "./AboutField";
import { BuildStatus } from "./BuildStatus";

interface ProjectMostRecentBuildProps {
  builds: AcdpBuildProjectBuild[];
}

const ProjectMostRecentBuildStatus = ({
  builds,
}: ProjectMostRecentBuildProps) => {
  return builds.length > 0 ? (
    <BuildStatus status={builds[0].buildStatus} />
  ) : (
    <></>
  );
};

const ProjectMostRecentBuildExecuted = ({
  builds,
}: ProjectMostRecentBuildProps) => {
  const build = builds.find((b) => b.startTime);
  return build
    ? `${formatDistanceStrict(new Date(build.startTime!), new Date())} ago`
    : "";
};

const ProjectMostRecentBuildDuration = ({
  builds,
}: ProjectMostRecentBuildProps) => {
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
          <ProjectMostRecentBuildStatus builds={builds} />
        </AboutField>
        <AboutField label="Last executed" gridSizes={{ xs: 12, sm: 6, lg: 4 }}>
          <ProjectMostRecentBuildExecuted builds={builds} />
        </AboutField>
        <AboutField label="Duration" gridSizes={{ xs: 12, sm: 6, lg: 4 }}>
          <ProjectMostRecentBuildDuration builds={builds} />
        </AboutField>
      </Grid>
    </Box>
  );
};
