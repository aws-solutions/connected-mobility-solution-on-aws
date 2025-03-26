// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { CampaignTargetType } from "@com.cms.fleetmanagement/api-server";
import {
  CampaignStatus,
  IoTFleetWiseClient,
} from "@aws-sdk/client-iotfleetwise";
import { listCampaignsForTarget } from "../list-campaigns-for-target";

// Mock the AWS SDK clients
jest.mock("@aws-sdk/client-iotfleetwise");

describe("listCampaignsForTarget", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("should return campaigns for a specific fleet target", async () => {
    // Mock data
    const targetId = "fleet-1";
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
        targetArn: "arn:aws:iotfleetwise:us-east-1:123456789012:fleet/fleet-1",
      },
    ];

    // Setup mocks
    IoTFleetWiseClient.prototype.send = jest.fn().mockResolvedValue({
      campaignSummaries: mockCampaignSummaries,
    });

    // Execute
    const result = await listCampaignsForTarget({
      targetType: CampaignTargetType.FLEET,
      targetId,
    });

    // Verify
    expect(result).toEqual({
      campaigns: [
        {
          targetId: "fleet-1",
          name: "campaign-1",
          status: CampaignStatus.RUNNING,
        },
        {
          targetId: "fleet-1",
          name: "campaign-3",
          status: CampaignStatus.SUSPENDED,
        },
      ],
    });

    // Verify calls
    expect(IoTFleetWiseClient.prototype.send).toHaveBeenCalledTimes(1);
  });

  it("should return campaigns for a specific vehicle target", async () => {
    // Mock data
    const targetId = "vehicle-1";
    const mockCampaignSummaries = [
      {
        name: "campaign-1",
        status: CampaignStatus.RUNNING,
        targetArn:
          "arn:aws:iotfleetwise:us-east-1:123456789012:vehicle/vehicle-1",
      },
      {
        name: "campaign-2",
        status: CampaignStatus.CREATING,
        targetArn:
          "arn:aws:iotfleetwise:us-east-1:123456789012:vehicle/vehicle-2",
      },
    ];

    // Setup mocks
    IoTFleetWiseClient.prototype.send = jest.fn().mockResolvedValue({
      campaignSummaries: mockCampaignSummaries,
    });

    // Execute
    const result = await listCampaignsForTarget({
      targetType: CampaignTargetType.VEHICLE,
      targetId,
    });

    // Verify
    expect(result).toEqual({
      campaigns: [
        {
          targetId: "vehicle-1",
          name: "campaign-1",
          status: CampaignStatus.RUNNING,
        },
      ],
    });

    // Verify calls
    expect(IoTFleetWiseClient.prototype.send).toHaveBeenCalledTimes(1);
  });

  it("should handle no matching campaigns", async () => {
    // Mock data
    const targetId = "fleet-3";
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
    ];

    // Setup mocks
    IoTFleetWiseClient.prototype.send = jest.fn().mockResolvedValue({
      campaignSummaries: mockCampaignSummaries,
    });

    // Execute
    const result = await listCampaignsForTarget({
      targetType: CampaignTargetType.FLEET,
      targetId,
    });

    // Verify
    expect(result).toEqual({ campaigns: [] });
    expect(IoTFleetWiseClient.prototype.send).toHaveBeenCalledTimes(1);
  });
});
