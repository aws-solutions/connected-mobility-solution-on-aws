// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {
  CampaignStatus,
  IoTFleetWiseClient,
} from "@aws-sdk/client-iotfleetwise";
import { listCampaigns } from "../list-campaigns";

// Mock the AWS SDK clients
jest.mock("@aws-sdk/client-iotfleetwise");

describe("listCampaigns", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("should return a list of campaigns", async () => {
    // Mock data
    const mockCampaignSummaries = [
      {
        name: "campaign-1",
        status: CampaignStatus.RUNNING,
        targetArn: "arn:aws:iotfleetwise:us-east-1:123456789012:fleet/fleet-1",
      },
      {
        name: "campaign-2",
        status: CampaignStatus.CREATING,
        targetArn: "arn:aws:iotfleetwise:us-east-1:123456789012:fleet/fleet-2",
      },
      {
        name: "campaign-3",
        status: CampaignStatus.SUSPENDED,
        targetArn:
          "arn:aws:iotfleetwise:us-east-1:123456789012:vehicle/vehicle-1",
      },
    ];

    // Setup mocks
    IoTFleetWiseClient.prototype.send = jest.fn().mockResolvedValue({
      campaignSummaries: mockCampaignSummaries,
    });

    // Execute
    const result = await listCampaigns();

    // Verify
    expect(result).toEqual({
      campaigns: [
        {
          targetId: "arn:aws:iotfleetwise:us-east-1:123456789012:fleet/fleet-1",
          name: "campaign-1",
          status: CampaignStatus.RUNNING,
        },
        {
          targetId: "arn:aws:iotfleetwise:us-east-1:123456789012:fleet/fleet-2",
          name: "campaign-2",
          status: CampaignStatus.CREATING,
        },
        {
          targetId:
            "arn:aws:iotfleetwise:us-east-1:123456789012:vehicle/vehicle-1",
          name: "campaign-3",
          status: CampaignStatus.SUSPENDED,
        },
      ],
    });

    // Verify calls
    expect(IoTFleetWiseClient.prototype.send).toHaveBeenCalledTimes(1);
  });

  it("should handle empty campaigns list", async () => {
    // Mock empty response
    IoTFleetWiseClient.prototype.send = jest.fn().mockResolvedValue({
      campaignSummaries: [],
    });

    // Execute
    const result = await listCampaigns();

    // Verify
    expect(result).toEqual({ campaigns: [] });
    expect(IoTFleetWiseClient.prototype.send).toHaveBeenCalledTimes(1);
  });
});
