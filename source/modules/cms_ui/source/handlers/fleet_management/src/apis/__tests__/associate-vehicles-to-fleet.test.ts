// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { associateVehiclesToFleet } from "../associate-vehicles-to-fleet";
import {
  AssociateVehiclesToFleetInput,
  FleetNotFound,
} from "@com.cms.fleetmanagement/api-server";
import {
  IoTFleetWiseClient,
  AssociateVehicleFleetCommand,
} from "@aws-sdk/client-iotfleetwise";

// Mock the AWS SDK
jest.mock("@aws-sdk/client-iotfleetwise");

describe("associateVehiclesToFleet", () => {
  // Setup mocks
  const mockSend = jest.fn();
  const mockIoTFleetWiseClient = IoTFleetWiseClient as jest.MockedClass<
    typeof IoTFleetWiseClient
  >;

  beforeEach(() => {
    // Clear all mocks before each test
    jest.clearAllMocks();

    // Setup the mock implementation
    mockIoTFleetWiseClient.prototype.send = mockSend;
    mockSend.mockResolvedValue({});
  });

  it("should associate vehicles to a fleet successfully", async () => {
    // Arrange
    const input: AssociateVehiclesToFleetInput = {
      id: "fleet-123",
      vehicleNames: ["vehicle-1", "vehicle-2"],
    };

    // Act
    const result = await associateVehiclesToFleet(input);

    // Assert
    expect(result).toEqual({});
    expect(mockSend).toHaveBeenCalledTimes(2);
    expect(mockIoTFleetWiseClient).toHaveBeenCalledTimes(1);

    // Verify the command was called with correct parameters for each vehicle
    expect(AssociateVehicleFleetCommand).toHaveBeenCalledWith({
      fleetId: "fleet-123",
      vehicleName: "vehicle-1",
    });
    expect(AssociateVehicleFleetCommand).toHaveBeenCalledWith({
      fleetId: "fleet-123",
      vehicleName: "vehicle-2",
    });
  });

  it("should throw FleetNotFound when association fails", async () => {
    // Arrange
    const input: AssociateVehiclesToFleetInput = {
      id: "invalid-fleet",
      vehicleNames: ["vehicle-1"],
    };

    // Setup mock to throw an error
    mockSend.mockRejectedValueOnce(new Error("Fleet not found"));

    // Act & Assert
    await expect(associateVehiclesToFleet(input)).rejects.toThrow(
      FleetNotFound,
    );
    expect(mockSend).toHaveBeenCalledTimes(1);
  });

  it("should include the correct error message and fleetId in the exception", async () => {
    // Arrange
    const fleetId = "fleet-404";
    const vehicleName = "vehicle-xyz";
    const input: AssociateVehiclesToFleetInput = {
      id: fleetId,
      vehicleNames: [vehicleName],
    };

    // Setup mock to throw an error
    mockSend.mockRejectedValueOnce(new Error("Some AWS error"));

    // Act & Assert
    try {
      await associateVehiclesToFleet(input);
      fail("Expected function to throw");
    } catch (error) {
      expect(error).toBeInstanceOf(FleetNotFound);
      expect(error.message).toContain(
        `Error associating vehicle ${vehicleName} to fleet ${fleetId}`,
      );
      expect(error.fleetId).toBe(fleetId);
    }
  });
});
