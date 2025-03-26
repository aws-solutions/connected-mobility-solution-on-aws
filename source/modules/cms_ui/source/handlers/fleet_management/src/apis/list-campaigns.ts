// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {
  CampaignItem,
  ListCampaignsOutput,
} from "@com.cms.fleetmanagement/api-server";
import {
  IoTFleetWiseClient,
  ListCampaignsCommand,
} from "@aws-sdk/client-iotfleetwise";

export async function listCampaigns(): Promise<ListCampaignsOutput> {
  const client = new IoTFleetWiseClient();
  const listCampaignsCommand = new ListCampaignsCommand();
  const campaigns = await client.send(listCampaignsCommand);
  return {
    campaigns: campaigns.campaignSummaries.map(
      (campaign) =>
        ({
          targetId: campaign.targetArn,
          name: campaign.name,
          status: campaign.status,
        }) as CampaignItem,
    ),
  };
}
