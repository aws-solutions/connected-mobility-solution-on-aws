// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { CampaignNotFound } from "@com.cms.fleetmanagement/api-server";
import {
  IoTFleetWiseClient,
  ResourceNotFoundException,
} from "@aws-sdk/client-iotfleetwise";
import { getCampaign } from "../get-campaign";

// Mock the AWS SDK clients and commands
jest.mock("@aws-sdk/client-iotfleetwise");

describe("getCampaign", () => {
  const mockSend = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    (IoTFleetWiseClient as jest.Mock).mockImplementation(() => ({
      send: mockSend,
    }));
  });

  it("should return campaign details when campaign exists", async () => {
    // Mock responses
    const campaignName = "test-campaign";
    const targetArn =
      "arn:aws:iotfleetwise:us-east-1:123456789012:fleet/test-fleet";

    mockSend.mockResolvedValue({
      name: campaignName,
      status: "RUNNING",
      targetArn,
    });

    // Execute
    const result = await getCampaign({ name: campaignName });

    // Verify
    expect(result).toEqual({
      name: campaignName,
      status: "RUNNING",
      targetId: targetArn,
    });
    expect(mockSend).toHaveBeenCalledTimes(1);
  });

  it("should throw CampaignNotFound when campaign does not exist", async () => {
    // Mock responses
    const campaignName = "non-existent-campaign";
    mockSend.mockImplementation(() => {
      throw new ResourceNotFoundException({
        message: "Resource not found",
        $metadata: {},
        resourceId: campaignName,
        resourceType: "CAMPAIGN",
      });
    });

    // Execute and verify
    await expect(getCampaign({ name: campaignName })).rejects.toThrow(
      CampaignNotFound,
    );
    expect(mockSend).toHaveBeenCalledTimes(1);
  });

  it("should propagate other errors", async () => {
    // Mock responses
    const campaignName = "error-campaign";
    const error = new Error("Network error");
    mockSend.mockRejectedValue(error);

    // Execute and verify
    await expect(getCampaign({ name: campaignName })).rejects.toThrow(
      "Network error",
    );
    expect(mockSend).toHaveBeenCalledTimes(1);
  });
});
