// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { LoggerService } from "@backstage/backend-plugin-api";
import { mockServices } from "@backstage/backend-test-utils";
import { Config } from "@backstage/config";
import { AwsCredentialProvider } from "@backstage/integration-aws-node";

import {
  mockCredentialsProvider,
  mockConfigWithMultiAccount,
} from "../../mocks";
import { AcdpAccountDirectoryService } from "../acdp-account-directory-service";

export class MockedAcdpAccountDirectoryService extends AcdpAccountDirectoryService {
  public constructor(
    config?: Config,
    awsCredentialsProvider?: AwsCredentialProvider,
    logger?: LoggerService,
  ) {
    super({
      config: config ?? mockConfigWithMultiAccount,
      awsCredentialsProvider: awsCredentialsProvider ?? mockCredentialsProvider,
      logger: logger ?? mockServices.logger.mock(),
    });
  }
}
