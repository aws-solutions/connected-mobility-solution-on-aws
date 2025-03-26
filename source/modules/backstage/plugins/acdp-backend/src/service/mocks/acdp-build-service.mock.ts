// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { LoggerService, UrlReaderService } from "@backstage/backend-plugin-api";
import { Config } from "@backstage/config";
import { ScmIntegrations } from "@backstage/integration";
import { AwsCredentialProvider } from "@backstage/integration-aws-node";
import { mockServices } from "@backstage/backend-test-utils";

import { AcdpBuildService } from "../acdp-build-service";
import {
  mockConfigWithoutMultiAccount,
  mockCredentialsProvider,
  mockIntegrations,
  mockUrlReader,
} from "../../mocks";
import { OperationalMetrics } from "../../utils/operational-metrics";

const mockOperationalMetrics: OperationalMetrics = {
  _metricsEndpoint: "XXXXXXXXXXXXXXXXXXXXX",
  _logger: mockServices.logger.mock(),
  _sendAnonymousMetrics: false,
  sendMetrics: jest.fn().mockResolvedValue(undefined),
} as unknown as OperationalMetrics;

export class MockedAcdpBuildService extends AcdpBuildService {
  public constructor(
    config?: Config,
    reader?: UrlReaderService,
    integrations?: ScmIntegrations,
    awsCredentialsProvider?: AwsCredentialProvider,
    logger?: LoggerService,
  ) {
    super({
      config: config ?? mockConfigWithoutMultiAccount,
      reader: reader ?? mockUrlReader,
      integrations: integrations ?? mockIntegrations,
      awsCredentialsProvider: awsCredentialsProvider ?? mockCredentialsProvider,
      logger: logger ?? mockServices.logger.mock(),
      operationalMetrics: mockOperationalMetrics,
    });
  }
}
