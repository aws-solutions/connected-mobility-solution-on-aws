// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { deleteCampaign } from "../delete-campaign";
import { CampaignNotFound } from "@com.cms.fleetmanagement/api-server";
import {
  IoTFleetWiseClient,
  DeleteCampaignCommand,
  ResourceNotFoundException,
} from "@aws-sdk/client-iotfleetwise";

// Mock the AWS SDK
jest.mock("@aws-sdk/client-iotfleetwise");

describe("deleteCampaign", () => {
  // Reset mocks before each test
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("should delete a campaign successfully", async () => {
    // Setup mock implementation
    const mockSend = jest.fn().mockResolvedValue({});
    (IoTFleetWiseClient as jest.Mock).mockImplementation(() => ({
      send: mockSend,
    }));

    // Call the function
    const result = await deleteCampaign({ name: "test-campaign" });

    // Verify the results
    expect(result).toBeUndefined();
    expect(IoTFleetWiseClient).toHaveBeenCalledTimes(1);
    expect(mockSend).toHaveBeenCalledTimes(1);
    expect(DeleteCampaignCommand).toHaveBeenCalledWith({
      name: "test-campaign",
    });
  });

  it("should throw CampaignNotFound when campaign doesn't exist", async () => {
    // Setup mock implementation to throw ResourceNotFoundException
    const mockSend = jest.fn().mockRejectedValue(
      new ResourceNotFoundException({
        message: "Resource not found",
        $metadata: {},
        resourceId: "non-existent-campaign",
        resourceType: "Campaign",
      }),
    );
    (IoTFleetWiseClient as jest.Mock).mockImplementation(() => ({
      send: mockSend,
    }));

    // Call the function and expect it to throw
    await expect(
      deleteCampaign({ name: "non-existent-campaign" }),
    ).rejects.toThrow(CampaignNotFound);

    // Verify the mock was called
    expect(IoTFleetWiseClient).toHaveBeenCalledTimes(1);
    expect(mockSend).toHaveBeenCalledTimes(1);
  });

  it("should propagate other errors", async () => {
    // Setup mock implementation to throw a different error
    const error = new Error("Some other error");
    const mockSend = jest.fn().mockRejectedValue(error);
    (IoTFleetWiseClient as jest.Mock).mockImplementation(() => ({
      send: mockSend,
    }));

    // Call the function and expect it to throw the original error
    await expect(deleteCampaign({ name: "test-campaign" })).rejects.toThrow(
      "Some other error",
    );

    // Verify the mock was called
    expect(IoTFleetWiseClient).toHaveBeenCalledTimes(1);
    expect(mockSend).toHaveBeenCalledTimes(1);
  });
});
