// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { Logger } from "winston";

import { UrlReader, getVoidLogger } from "@backstage/backend-common";
import { Config } from "@backstage/config";
import { ScmIntegrations } from "@backstage/integration";
import { AwsCredentialProvider } from "@backstage/integration-aws-node";

import { AcdpBuildService } from "../acdp-build-service";
import {
  mockConfig,
  mockCredentialsProvider,
  mockIntegrations,
  mockUrlReader,
} from "../../mocks";

export class MockedAcdpBuildService extends AcdpBuildService {
  public constructor(
    config?: Config,
    reader?: UrlReader,
    integrations?: ScmIntegrations,
    awsCredentialsProvider?: AwsCredentialProvider,
    logger?: Logger,
  ) {
    super({
      config: config ?? mockConfig,
      reader: reader ?? mockUrlReader,
      integrations: integrations ?? mockIntegrations,
      awsCredentialsProvider: awsCredentialsProvider ?? mockCredentialsProvider,
      logger: logger ?? getVoidLogger(),
    });
  }
}
