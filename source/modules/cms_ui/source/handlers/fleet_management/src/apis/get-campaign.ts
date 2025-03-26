// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {
  CampaignItem,
  GetCampaignInput,
  CampaignNotFound,
} from "@com.cms.fleetmanagement/api-server";
import {
  IoTFleetWiseClient,
  GetCampaignCommand,
  ResourceNotFoundException,
} from "@aws-sdk/client-iotfleetwise";

export async function getCampaign(
  input: GetCampaignInput,
): Promise<CampaignItem> {
  const client = new IoTFleetWiseClient();
  const getCampaignCommand = new GetCampaignCommand({ name: input.name });
  try {
    const campaign = await client.send(getCampaignCommand);
    return {
      name: campaign.name,
      status: campaign.status,
      targetId: campaign.targetArn,
    };
  } catch (e) {
    if (e instanceof ResourceNotFoundException) {
      throw new CampaignNotFound({
        message: "Campaign not found.",
        campaignName: input.name,
      });
    }
    throw e;
  }
}
