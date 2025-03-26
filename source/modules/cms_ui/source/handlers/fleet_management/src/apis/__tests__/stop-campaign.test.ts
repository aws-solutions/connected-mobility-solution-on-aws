// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { stopCampaign } from "../stop-campaign";
import {
  CampaignNotFound,
  CampaignBeingModified,
} from "@com.cms.fleetmanagement/api-server";
import {
  IoTFleetWiseClient,
  UpdateCampaignCommand,
  ResourceNotFoundException,
  ConflictException,
} from "@aws-sdk/client-iotfleetwise";

// Mock the AWS SDK
jest.mock("@aws-sdk/client-iotfleetwise");

describe("stopCampaign", () => {
  const mockSend = jest.fn();
  const mockInput = { name: "test-campaign" };

  beforeEach(() => {
    jest.clearAllMocks();
    // Setup the mock implementation
    (IoTFleetWiseClient as jest.Mock).mockImplementation(() => ({
      send: mockSend,
    }));

    // Reset mock for each test
    mockSend.mockReset();
  });

  it("should successfully stop a campaign", async () => {
    // Setup mock to resolve successfully
    mockSend.mockImplementation((command) => {
      return Promise.resolve({});
    });

    // Call the function
    const result = await stopCampaign(mockInput);

    // Verify the client was called with correct parameters
    expect(IoTFleetWiseClient).toHaveBeenCalledTimes(1);
    expect(mockSend).toHaveBeenCalledTimes(1);

    const commandArg = mockSend.mock.calls[0][0];
    expect(commandArg).toBeInstanceOf(UpdateCampaignCommand);

    // Verify the result
    expect(result).toBeUndefined();
  });

  it("should throw CampaignNotFound when campaign doesn't exist", async () => {
    // Setup mock to throw ResourceNotFoundException
    const error = new ResourceNotFoundException({
      message: "Resource not found",
      $metadata: {},
      resourceId: "test-campaign",
      resourceType: "Campaign",
    });
    mockSend.mockImplementation(() => {
      throw error;
    });

    // Call and verify exception
    await expect(stopCampaign(mockInput)).rejects.toThrow(CampaignNotFound);
    await expect(stopCampaign(mockInput)).rejects.toMatchObject({
      campaignName: mockInput.name,
    });
  });

  it("should throw CampaignBeingModified when campaign is being modified", async () => {
    // Setup mock to throw ConflictException
    const error = new ConflictException({
      message: "Conflict detected",
      $metadata: {},
      resourceType: "Campaign",
      resource: "test-campaign",
    });
    mockSend.mockImplementation(() => {
      throw error;
    });

    // Call and verify exception
    await expect(stopCampaign(mockInput)).rejects.toThrow(
      CampaignBeingModified,
    );
    await expect(stopCampaign(mockInput)).rejects.toMatchObject({
      campaignName: mockInput.name,
    });
  });

  it("should propagate unknown errors", async () => {
    // Setup mock to throw an unknown error
    const error = new Error("Unknown error");
    mockSend.mockImplementation(() => {
      throw error;
    });

    // Call and verify exception
    await expect(stopCampaign(mockInput)).rejects.toThrow("Unknown error");
  });
});
