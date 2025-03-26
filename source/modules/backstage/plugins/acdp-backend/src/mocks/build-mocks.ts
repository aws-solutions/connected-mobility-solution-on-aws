// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

export const mockedConfigDataWithMultiAccount = {
  acdp: {
    s3Catalog: {
      bucketName: "bucket",
      prefix: "test/backstage/catalog",
      region: "us-west-2",
    },
    buildConfig: {
      buildConfigStoreSsmPrefix: "/local/backstage/acdp-build",
    },
    deploymentDefaults: {
      region: "us-west-2",
      accountId: "111111111111",
      codeBuildProjectArn:
        "arn:aws:codebuild:us-west-2:111111111111:project/test",
    },
    accountDirectory: {
      enableMultiAccountDeployment: "true",
      organizationsAccountId: "1111111111111",
      organizationsManagementAccountRegion: "us-east-1",
      organizationsAccountAssumeRoleName: "acdp-orgs-assume-role",
      availableRegionsParameterName: "/solution/regions",
      enrolledOrgsParameterName: "/solution/ous",
      metricsRoleName: "acdp-metrics-role",
    },
    operationalMetrics: {
      solutionVersion: "vX.X",
      solutionId: "001",
      deploymentUuid: "uuid",
      sendAnonymousMetrics: "false",
    },
    metrics: {
      userAgentString: "local-user-agent",
    },
  },
  techdocs: {
    generator: {
      runIn: "local",
    },
    builder: "local",
    publisher: {
      type: "awsS3",
      awsS3: {
        bucketName: "bucket",
        region: "us-west-2",
        bucketRootPath: "test/backstage/techdocs",
      },
    },
  },
};

export const mockedConfigDataWithoutMultiAccount = {
  acdp: {
    s3Catalog: {
      bucketName: "bucket",
      prefix: "test/backstage/catalog",
      region: "us-west-2",
    },
    buildConfig: {
      buildConfigStoreSsmPrefix: "/local/backstage/acdp-build",
    },
    deploymentDefaults: {
      region: "us-west-2",
      accountId: "111111111111",
      codeBuildProjectArn:
        "arn:aws:codebuild:us-west-2:111111111111:project/test",
    },
    accountDirectory: {
      enableMultiAccountDeployment: "false",
      organizationsAccountId: null,
      organizationsManagementAccountRegion: null,
      organizationsAccountAssumeRoleName: null,
      availableRegionsParameterName: null,
      enrolledOrgsParameterName: null,
      metricsRoleName: "acdp-metrics-role",
    },
    operationalMetrics: {
      solutionVersion: "vX.X",
      solutionId: "001",
      deploymentUuid: "uuid",
      sendAnonymousMetrics: "false",
    },
    metrics: {
      userAgentString: "local-user-agent",
    },
  },
  techdocs: {
    generator: {
      runIn: "local",
    },
    builder: "local",
    publisher: {
      type: "awsS3",
      awsS3: {
        bucketName: "bucket",
        region: "us-west-2",
        bucketRootPath: "test/backstage/techdocs",
      },
    },
  },
};
