// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {
  CampaignItem,
  ListCampaignsForTargetInput,
  ListCampaignsForTargetOutput,
} from "@com.cms.fleetmanagement/api-server";
import {
  IoTFleetWiseClient,
  ListCampaignsCommand,
} from "@aws-sdk/client-iotfleetwise";

export async function listCampaignsForTarget(
  input: ListCampaignsForTargetInput,
): Promise<ListCampaignsForTargetOutput> {
  const client = new IoTFleetWiseClient();
  const listCampaignsCommand = new ListCampaignsCommand();
  const campaigns = await client.send(listCampaignsCommand);
  return {
    campaigns: campaigns.campaignSummaries
      .filter((campaign) => {
        const [arnPrefix, targetId] = campaign.targetArn.split("/").slice(-2);
        const targetType = arnPrefix.split(":").pop();
        return (
          targetType === input.targetType.toLowerCase() &&
          targetId == input.targetId
        );
      })
      .map(
        (campaign) =>
          ({
            targetId: input.targetId,
            name: campaign.name,
            status: campaign.status,
          }) as CampaignItem,
      ),
  };
}
