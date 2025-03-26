// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { formatDistanceStrict } from "date-fns";

import { Link } from "@material-ui/core";

import { Table, TableColumn } from "@backstage/core-components";

import { AcdpBuildProjectBuild } from "backstage-plugin-acdp-common";

import { BuildStatus } from "./BuildStatus";

interface BuildHistoryTableProps {
  region: string;
  accountId: string;
  project: string | undefined;
  builds: AcdpBuildProjectBuild[];
  buildHistoryLength: number;
}

interface IndexedBuild extends AcdpBuildProjectBuild {
  index?: number;
}

export const BuildHistoryTable = (props: BuildHistoryTableProps) => {
  const { region, accountId, project, builds, buildHistoryLength } = props;
  const indexedBuilds = (builds.slice(0, buildHistoryLength) ?? []).map(
    (build, index) => ({ ...build, index: builds.length - index }),
  );

  const columns: TableColumn[] = [
    {
      title: "Module Build Number",
      field: "moduleBuildNumber",
      render: (row: IndexedBuild) => `#${row.index}`,
    },
    {
      title: "Project Build Number",
      field: "projectBuildNumber",
      render: (row: IndexedBuild) => {
        return (
          <Link
            href={`https://${region}.console.aws.amazon.com/codesuite/codebuild/${accountId}/projects/${project}/build/${row.id}/?region=${region}`}
            target="_blank"
          >
            #{row.buildNumber}
          </Link>
        );
      },
    },
    {
      title: "Status",
      field: "deploymentStatus",
      render: (row: IndexedBuild) => <BuildStatus status={row.buildStatus} />,
    },
    {
      title: "Duration",
      field: "duration",
      render: (row: IndexedBuild) =>
        row.startTime && row.endTime
          ? formatDistanceStrict(new Date(row.endTime), new Date(row.startTime))
          : "",
    },
  ];

  return (
    <Table
      options={{
        paging: false,
        search: false,
        toolbar: false,
        padding: "dense",
      }}
      data={indexedBuilds}
      columns={columns}
    />
  );
};
