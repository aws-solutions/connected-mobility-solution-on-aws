// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { LoggerService } from "@backstage/backend-plugin-api/index";
import { Config } from "@backstage/config";
import { MetricsData, MetricsMessage } from "backstage-plugin-acdp-common";
import axios from "axios";

export interface OperationalMetricsProps {
  config: Config;
  logger: LoggerService;
}

export class OperationalMetrics {
  private _metricsEndpoint: string =
    "https://metrics.awssolutionsbuilder.com/generic";
  private _solutionVersion?: string;
  private _solutionId?: string;
  private _deploymentUuid?: string;
  private _sendAnonymousMetrics: boolean;
  private _logger: LoggerService;

  constructor(props: OperationalMetricsProps) {
    const { config, logger } = props;
    this._logger = logger;
    this._sendAnonymousMetrics = config.getBoolean(
      "acdp.operationalMetrics.sendAnonymousMetrics",
    );
    if (this._sendAnonymousMetrics) {
      this._solutionId = config.getString("acdp.operationalMetrics.solutionId");
      this._deploymentUuid = config.getString(
        "acdp.operationalMetrics.deploymentUuid",
      );
      this._solutionVersion = config.getString(
        "acdp.operationalMetrics.solutionVersion",
      );
    }
  }

  public async sendMetrics(metricData: MetricsData): Promise<any> {
    if (!this._sendAnonymousMetrics) {
      return;
    }

    const formatted_timestamp = new Date()
      .toISOString()
      .replace("T", " ")
      .replace("Z", ""); // "%Y-%m-%d %H:%M:%S.%f"
    const metric_post_data: MetricsMessage = {
      solution: this._solutionId ?? "",
      uuid: this._deploymentUuid ?? "",
      timestamp: formatted_timestamp,
      version: this._solutionVersion ?? "",
      data: metricData,
    };

    const requestedTimeOut = 10 * 1000;
    try {
      await axios.post(
        this._metricsEndpoint,
        JSON.stringify(metric_post_data),
        {
          headers: {
            "Content-Type": "application/json",
          },
          timeout: requestedTimeOut,
        },
      );
    } catch (error) {
      this._logger.error(`Failed to send metrics: ${error}`);
    }
  }
}
