// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {
  StartCampaignInput,
  CampaignNotFound,
  CampaignBeingModified,
} from "@com.cms.fleetmanagement/api-server";
import {
  IoTFleetWiseClient,
  UpdateCampaignAction,
  UpdateCampaignCommand,
  ResourceNotFoundException,
  ConflictException,
} from "@aws-sdk/client-iotfleetwise";

export async function startCampaign(input: StartCampaignInput): Promise<{}> {
  const client = new IoTFleetWiseClient();
  const command = new UpdateCampaignCommand({
    name: input.name,
    action: UpdateCampaignAction.RESUME,
  });
  try {
    await client.send(command);
    return;
  } catch (e) {
    if (e instanceof ResourceNotFoundException) {
      throw new CampaignNotFound({
        message: "Campaign not found.",
        campaignName: input.name,
      });
    } else if (e instanceof ConflictException) {
      throw new CampaignBeingModified({
        message: "Campaign undergoing modification now, try again in sometime.",
        campaignName: input.name,
      });
    }
    throw e;
  }
}
