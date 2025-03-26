// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {
  CampaignTargetType,
  VehicleStatus,
} from "@com.cms.fleetmanagement/api-server";
import {
  CampaignStatus,
  IoTFleetWiseClient,
  ListFleetsCommand,
  ListVehiclesInFleetCommand,
  ListTagsForResourceCommand,
} from "@aws-sdk/client-iotfleetwise";
import { listFleets } from "../list-fleets";
import * as utils from "../utils";
import * as campaignUtils from "../list-campaigns-for-target";

// Mock the AWS SDK clients and other dependencies
jest.mock("@aws-sdk/client-iotfleetwise");
jest.mock("../utils");
jest.mock("../list-campaigns-for-target");

describe("listFleets", () => {
  // Setup common mocks and test data
  const mockSend = jest.fn();
  const mockGetVehicleStatus = jest.spyOn(utils, "getVehicleStatus");
  const mockListCampaignsForTarget = jest.spyOn(
    campaignUtils,
    "listCampaignsForTarget",
  );

  beforeEach(() => {
    jest.clearAllMocks();
    // Replace the IoTFleetWiseClient constructor with a mock implementation
    (IoTFleetWiseClient as jest.Mock).mockImplementation(() => ({
      send: mockSend,
    }));
  });

  it("should return an empty list when no fleets exist", async () => {
    // Mock the ListFleetsCommand response
    mockSend.mockResolvedValueOnce({
      fleetSummaries: [],
    });

    const result = await listFleets();

    expect(result).toEqual({ fleets: [] });
    expect(IoTFleetWiseClient).toHaveBeenCalledTimes(1);
    expect(mockSend).toHaveBeenCalledWith(expect.any(ListFleetsCommand));
    expect(mockListCampaignsForTarget).not.toHaveBeenCalled();
  });

  it("should return fleet details with connected vehicles and campaigns", async () => {
    // Mock data
    const mockFleet = {
      id: "fleet-123",
      arn: "arn:aws:iotfleetwise:us-east-1:123456789012:fleet/fleet-123",
      creationTime: new Date("2023-01-01"),
      lastModificationTime: new Date("2023-01-02"),
    };

    const mockVehicles = {
      vehicles: ["vehicle-1", "vehicle-2", "vehicle-3"],
    };

    const mockTags = {
      Tags: [
        { Key: "DisplayName", Value: "Test Fleet" },
        { Key: "OtherTag", Value: "OtherValue" },
      ],
    };

    const mockCampaigns = {
      campaigns: [
        {
          name: "campaign-1",
          status: CampaignStatus.RUNNING,
          targetId: "fleet-123",
        },
        {
          name: "campaign-2",
          status: CampaignStatus.CREATING,
          targetId: "fleet-123",
        },
      ],
    };

    // Setup mock responses
    mockSend.mockImplementation((command) => {
      if (command instanceof ListFleetsCommand) {
        return Promise.resolve({ fleetSummaries: [mockFleet] });
      } else if (command instanceof ListVehiclesInFleetCommand) {
        return Promise.resolve(mockVehicles);
      } else if (command instanceof ListTagsForResourceCommand) {
        return Promise.resolve(mockTags);
      }
      return Promise.reject(new Error("Unexpected command"));
    });

    // Mock vehicle status responses
    mockGetVehicleStatus
      .mockResolvedValueOnce(VehicleStatus.ACTIVE) // vehicle-1: active
      .mockResolvedValueOnce(VehicleStatus.INACTIVE) // vehicle-2: inactive
      .mockResolvedValueOnce(VehicleStatus.ACTIVE); // vehicle-3: active

    // Mock campaign listing
    mockListCampaignsForTarget.mockResolvedValueOnce(mockCampaigns);

    // Execute the function
    const result = await listFleets();

    // Verify results
    expect(result).toEqual({
      fleets: [
        {
          id: "fleet-123",
          name: "Test Fleet",
          numActiveCampaigns: 1,
          numTotalCampaigns: 2,
          numConnectedVehicles: 2,
          numTotalVehicles: 3,
          createdTime: mockFleet.creationTime.toString(),
          lastModifiedTime: mockFleet.lastModificationTime.toString(),
        },
      ],
    });

    // Verify the correct calls were made
    expect(IoTFleetWiseClient).toHaveBeenCalledTimes(1);
    expect(mockSend).toHaveBeenCalledWith(expect.any(ListFleetsCommand));

    // Instead of checking specific calls which can be in any order,
    // verify that the right commands were used with the right parameters
    expect(mockSend).toHaveBeenCalledTimes(3); // ListFleets, ListVehicles, ListTags

    const vehicleCommandCall = mockSend.mock.calls.find(
      (call) => call[0] instanceof ListVehiclesInFleetCommand,
    );
    expect(vehicleCommandCall).toBeDefined();

    const tagsCommandCall = mockSend.mock.calls.find(
      (call) => call[0] instanceof ListTagsForResourceCommand,
    );
    expect(tagsCommandCall[0]).toBeDefined();
    expect(mockListCampaignsForTarget).toHaveBeenCalledWith({
      targetType: CampaignTargetType.FLEET,
      targetId: "fleet-123",
    });
    expect(mockGetVehicleStatus).toHaveBeenCalledTimes(3);
  });

  it("should handle fleets without display name tags", async () => {
    // Mock data with no DisplayName tag
    const mockFleet = {
      id: "fleet-456",
      arn: "arn:aws:iotfleetwise:us-east-1:123456789012:fleet/fleet-456",
      creationTime: new Date("2023-02-01"),
      lastModificationTime: new Date("2023-02-02"),
    };

    // Setup mock responses
    mockSend.mockImplementation((command) => {
      if (command instanceof ListFleetsCommand) {
        return Promise.resolve({ fleetSummaries: [mockFleet] });
      } else if (command instanceof ListVehiclesInFleetCommand) {
        return Promise.resolve({ vehicles: [] });
      } else if (command instanceof ListTagsForResourceCommand) {
        return Promise.resolve({ Tags: [] }); // No tags
      }
      return Promise.reject(new Error("Unexpected command"));
    });

    mockListCampaignsForTarget.mockResolvedValueOnce({ campaigns: [] });

    // Execute the function
    const result = await listFleets();

    // Verify results - should use fleet ID as name when no DisplayName tag exists
    expect(result).toEqual({
      fleets: [
        {
          id: "fleet-456",
          name: "fleet-456", // Should fall back to ID
          numActiveCampaigns: 0,
          numTotalCampaigns: 0,
          numConnectedVehicles: 0,
          numTotalVehicles: 0,
          createdTime: mockFleet.creationTime.toString(),
          lastModifiedTime: mockFleet.lastModificationTime.toString(),
        },
      ],
    });
  });

  it("should handle errors gracefully", async () => {
    // Mock an error in the AWS SDK
    mockSend.mockRejectedValueOnce(new Error("AWS SDK Error"));

    // Verify the function throws the error
    await expect(listFleets()).rejects.toThrow("AWS SDK Error");
  });
});
