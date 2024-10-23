// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { createApiRef } from "@backstage/core-plugin-api";
import { AcdpApplication } from "backstage-plugin-acdp-common";

import { AcdpBaseApi, AcdpBaseApiInput } from "./AcdpBaseApi";

export const acdpMetricsApiRef = createApiRef<AcdpMetricsApi>({
  id: "plugin.acdpmetrics.service",
});

export class AcdpMetricsApi extends AcdpBaseApi {
  public constructor(options: AcdpBaseApiInput) {
    super(options);
  }

  async getApplicationByEntity({
    entityRef,
  }: {
    entityRef: string;
  }): Promise<AcdpApplication> {
    const searchParams = new URLSearchParams({
      entityRef: entityRef,
    });
    const urlSegment = `/application/by-entity?${searchParams}`;

    return await this._fetch<AcdpApplication>(urlSegment);
  }

  async getApplicationByArn(arn: string): Promise<AcdpApplication> {
    const searchParams = new URLSearchParams({
      arn: arn,
    });
    const urlSegment = `/application/by-arn?${searchParams}`;

    return await this._fetch<AcdpApplication>(urlSegment);
  }

  async getNetUnblendedCurrentMonthCost({
    entityRef,
    awsApplicationTag,
  }: {
    entityRef: string;
    awsApplicationTag: string;
  }): Promise<string> {
    const searchParams = new URLSearchParams({
      entityRef: entityRef,
      awsApplicationTag: awsApplicationTag,
    });
    const urlSegment = `/cost/current-month-net-unblended?${searchParams}`;

    return await this._fetch<string>(urlSegment);
  }
}
