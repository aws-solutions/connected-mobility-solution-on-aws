// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { LoggerService } from "@backstage/backend-plugin-api";
import { Config } from "@backstage/config";
import { AwsCredentialProvider } from "@backstage/integration-aws-node";
import { fromTemporaryCredentials } from "@aws-sdk/credential-providers";
import {
  OrganizationsClient,
  ListAccountsForParentCommand,
} from "@aws-sdk/client-organizations";
import { SSMClient, GetParameterCommand } from "@aws-sdk/client-ssm";
import { AcdpBaseService } from "./acdp-base-service";
import { awsApiCallWithErrorHandling } from "../utils";
import { AvailableAccountsProps } from "backstage-plugin-acdp-common";

export interface AcdpAccountDirectoryServiceOptions {
  config: Config;
  awsCredentialsProvider: AwsCredentialProvider;
  logger: LoggerService;
}

export class AcdpAccountDirectoryService extends AcdpBaseService {
  enableMultiAccountDeployment: boolean;
  organizationsManagementAccountRegion: string = "";
  organizationsAccountId: string = "";
  organizationsRoleArn: string = "";
  availableRegionsParameterName: string = "";
  enrolledOrgsParameterName: string = "";

  constructor(options: AcdpAccountDirectoryServiceOptions) {
    super({
      ...options,
      userAgentString: options.config.getString("acdp.metrics.userAgentString"),
    });

    this.enableMultiAccountDeployment = options.config.getBoolean(
      "acdp.accountDirectory.enableMultiAccountDeployment",
    );
    if (this.enableMultiAccountDeployment) {
      this.organizationsManagementAccountRegion = options.config.getString(
        "acdp.accountDirectory.organizationsManagementAccountRegion",
      );
      this.organizationsAccountId = options.config.getString(
        "acdp.accountDirectory.organizationsAccountId",
      );
      this.organizationsRoleArn = `arn:aws:iam::${
        this.organizationsAccountId
      }:role/${options.config.getString(
        "acdp.accountDirectory.organizationsAccountAssumeRoleName",
      )}`;
      this.availableRegionsParameterName = options.config.getString(
        "acdp.accountDirectory.availableRegionsParameterName",
      );
      this.enrolledOrgsParameterName = options.config.getString(
        "acdp.accountDirectory.enrolledOrgsParameterName",
      );
    }
  }

  public async getAvailableAccounts(): Promise<AvailableAccountsProps[]> {
    return this.enableMultiAccountDeployment
      ? this.getAvailableAccountsFromOrgs()
      : this.getDefaultAccount();
  }

  public async getAvailableRegions(): Promise<string[]> {
    return this.enableMultiAccountDeployment
      ? this.getAvailableRegionsFromOrgs()
      : this.getDefaultRegion();
  }

  private async getDefaultAccount(): Promise<AvailableAccountsProps[]> {
    return [
      {
        awsAccountId: this._defaultDeploymentTarget.awsAccountId,
        alias: "DEFAULT",
      },
    ];
  }

  private async getDefaultRegion(): Promise<string[]> {
    return [this._defaultDeploymentTarget.awsRegion];
  }

  private getOrganizationsClient(): OrganizationsClient {
    return new OrganizationsClient({
      region: this.organizationsManagementAccountRegion,
      customUserAgent: this._userAgentString,
      credentials: fromTemporaryCredentials({
        params: {
          RoleArn: this.organizationsRoleArn,
        },
      }),
    });
  }

  private getSSMClient(): SSMClient {
    return new SSMClient({
      region: this.organizationsManagementAccountRegion,
      customUserAgent: this._userAgentString,
      credentials: fromTemporaryCredentials({
        params: {
          RoleArn: this.organizationsRoleArn,
        },
      }),
    });
  }

  private async getAvailableRegionsFromOrgs(): Promise<string[]> {
    const ssmClient = this.getSSMClient();

    const availableRegionsQueryResult = await awsApiCallWithErrorHandling(
      () =>
        ssmClient.send(
          new GetParameterCommand({
            Name: this.availableRegionsParameterName,
          }),
        ),
      `Could not get available regions from ssm parameter: ${this.availableRegionsParameterName}`,
      this._logger,
    );

    const availableRegions =
      availableRegionsQueryResult.Parameter?.Value?.split(",");

    return availableRegions || [];
  }

  private async getAvailableAccountsFromOrgs(): Promise<
    AvailableAccountsProps[]
  > {
    const organizationsClient = this.getOrganizationsClient();

    const ssmClient = this.getSSMClient();

    const enrolledOUList = await awsApiCallWithErrorHandling(
      () =>
        ssmClient.send(
          new GetParameterCommand({
            Name: this.enrolledOrgsParameterName,
          }),
        ),
      `Could not get available organizational units from ssm parameter: ${this.enrolledOrgsParameterName}`,
      this._logger,
    );

    const formattedAvailableAccounts: AvailableAccountsProps[] = [];

    if (enrolledOUList.Parameter?.Value) {
      for (const ouId of enrolledOUList.Parameter.Value.split(",")) {
        if (ouId) {
          const availableAccounts = await awsApiCallWithErrorHandling(
            () =>
              organizationsClient.send(
                new ListAccountsForParentCommand({
                  ParentId: ouId,
                }),
              ),
            `Could not get Accounts of parent: ${ouId}`,
            this._logger,
          );

          if (availableAccounts.Accounts) {
            for (const account of availableAccounts.Accounts) {
              formattedAvailableAccounts.push({
                awsAccountId: account.Id ?? "",
                alias: account.Name ?? "",
              });
            }
          }
        }
      }
    }

    return formattedAvailableAccounts;
  }
}
