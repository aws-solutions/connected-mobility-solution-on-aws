// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { Config } from "@backstage/config";
import { AcdpBuildService } from "../acdp-build-service";
import { UrlReader, getVoidLogger } from "@backstage/backend-common";
import { ScmIntegrations } from "@backstage/integration";
import { AwsCredentialProvider } from "@backstage/integration-aws-node";
import { Logger } from "winston";
import {
  mockConfig,
  mockCredentialsProvider,
  mockIntegrations,
  mockUrlReader,
} from "../../__mocks__/common-mocks";
import { Entity } from "@backstage/catalog-model";

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

  public getSsmParameterNameForEntityBuildParameters(entity: Entity) {
    return super.getSsmParameterNameForEntityBuildParameters(entity);
  }

  public getSsmParameterNameForEntitySourceConfig(entity: Entity) {
    return super.getSsmParameterNameForEntitySourceConfig(entity);
  }
}
