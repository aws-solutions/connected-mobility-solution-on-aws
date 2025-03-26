// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {
  FleetNotFound,
  VehicleStatus,
} from "@com.cms.fleetmanagement/api-server";
import {
  IoTFleetWiseClient,
  ResourceNotFoundException,
} from "@aws-sdk/client-iotfleetwise";
import { getFleet } from "../get-fleet";
import { getVehicleStatus } from "../utils";
import { listCampaignsForTarget } from "../list-campaigns-for-target";

// Mock the AWS SDK clients and commands
jest.mock("@aws-sdk/client-iotfleetwise");
jest.mock("../utils");
jest.mock("../list-campaigns-for-target");

describe("getFleet", () => {
  const mockSend = jest.fn();
  const mockGetVehicleStatus = jest.fn();
  const mockListCampaignsForTarget = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    (IoTFleetWiseClient as jest.Mock).mockImplementation(() => ({
      send: mockSend,
    }));
    (getVehicleStatus as jest.Mock).mockImplementation(mockGetVehicleStatus);
    (listCampaignsForTarget as jest.Mock).mockImplementation(
      mockListCampaignsForTarget,
    );
  });

  it("should return fleet details when fleet exists", async () => {
    // Mock responses
    const fleetId = "test-fleet";
    const fleetArn =
      "arn:aws:iotfleetwise:us-east-1:123456789012:fleet/test-fleet";
    const creationTime = new Date("2023-01-01");
    const lastModificationTime = new Date("2023-01-02");

    mockSend.mockImplementation((command) => {
      if (command.constructor.name === "GetFleetCommand") {
        return {
          id: fleetId,
          arn: fleetArn,
          description: "Test Fleet Description",
          creationTime,
          lastModificationTime,
        };
      } else if (command.constructor.name === "ListTagsForResourceCommand") {
        return {
          Tags: [
            { Key: "DisplayName", Value: "Test Fleet Display Name" },
            { Key: "Environment", Value: "Production" },
          ],
        };
      } else if (command.constructor.name === "ListVehiclesInFleetCommand") {
        return {
          vehicles: ["vehicle1", "vehicle2", "vehicle3"],
        };
      }
    });

    mockListCampaignsForTarget.mockResolvedValue({
      campaigns: [
        { name: "campaign1", status: "RUNNING" },
        { name: "campaign2", status: "COMPLETED" },
      ],
    });

    // Mock getVehicleStatus to return ACTIVE for vehicle1 and vehicle2
    mockGetVehicleStatus.mockImplementation((vehicleName) => {
      if (vehicleName === "vehicle1" || vehicleName === "vehicle2") {
        return Promise.resolve(VehicleStatus.ACTIVE);
      }
      return Promise.resolve(VehicleStatus.INACTIVE);
    });

    // Execute
    const result = await getFleet({ id: fleetId });

    // Verify
    expect(result).toEqual({
      id: fleetId,
      name: "Test Fleet Display Name",
      numActiveCampaigns: 1,
      numTotalCampaigns: 2,
      numConnectedVehicles: 2,
      numTotalVehicles: 3,
      createdTime: creationTime.toString(),
      lastModifiedTime: lastModificationTime.toString(),
      description: "Test Fleet Description",
      tags: [
        { Key: "DisplayName", Value: "Test Fleet Display Name" },
        { Key: "Environment", Value: "Production" },
      ],
    });
    expect(mockSend).toHaveBeenCalledTimes(3);
    expect(mockListCampaignsForTarget).toHaveBeenCalledWith({
      targetType: "FLEET",
      targetId: fleetId,
    });
  });

  it("should use fleet ID as name when DisplayName tag is not present", async () => {
    // Mock responses
    const fleetId = "test-fleet";
    const fleetArn =
      "arn:aws:iotfleetwise:us-east-1:123456789012:fleet/test-fleet";

    mockSend.mockImplementation((command) => {
      if (command.constructor.name === "GetFleetCommand") {
        return {
          id: fleetId,
          arn: fleetArn,
          description: "",
          creationTime: new Date(),
          lastModificationTime: new Date(),
        };
      } else if (command.constructor.name === "ListTagsForResourceCommand") {
        return {
          Tags: [{ Key: "Environment", Value: "Production" }],
        };
      } else if (command.constructor.name === "ListVehiclesInFleetCommand") {
        return {
          vehicles: [],
        };
      }
    });

    mockListCampaignsForTarget.mockResolvedValue({
      campaigns: [],
    });

    // Execute
    const result = await getFleet({ id: fleetId });

    // Verify
    expect(result.name).toEqual(fleetId);
  });

  it("should throw FleetNotFound when fleet does not exist", async () => {
    // Mock responses
    const fleetId = "non-existent-fleet";
    mockSend.mockImplementation(() => {
      throw new ResourceNotFoundException({
        message: "Resource not found",
        $metadata: {},
        resourceId: fleetId,
        resourceType: "FLEET",
      });
    });

    // Execute and verify
    await expect(getFleet({ id: fleetId })).rejects.toThrow(FleetNotFound);
    expect(mockSend).toHaveBeenCalledTimes(1);
  });

  it("should propagate other errors", async () => {
    // Mock responses
    const fleetId = "error-fleet";
    const error = new Error("Network error");
    mockSend.mockRejectedValue(error);

    // Execute and verify
    await expect(getFleet({ id: fleetId })).rejects.toThrow("Network error");
    expect(mockSend).toHaveBeenCalledTimes(1);
  });
});
