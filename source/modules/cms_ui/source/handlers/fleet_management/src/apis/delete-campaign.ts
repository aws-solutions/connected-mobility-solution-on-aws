// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {
  DeleteCampaignInput,
  CampaignNotFound,
} from "@com.cms.fleetmanagement/api-server";
import {
  IoTFleetWiseClient,
  DeleteCampaignCommand,
  ResourceNotFoundException,
} from "@aws-sdk/client-iotfleetwise";

export async function deleteCampaign(input: DeleteCampaignInput): Promise<{}> {
  const client = new IoTFleetWiseClient();
  const command = new DeleteCampaignCommand({ name: input.name });
  try {
    await client.send(command);
    return;
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
