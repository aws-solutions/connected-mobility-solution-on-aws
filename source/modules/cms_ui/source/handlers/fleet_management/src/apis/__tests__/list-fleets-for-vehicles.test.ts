// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { VehicleNotFound } from "@com.cms.fleetmanagement/api-server";
import {
  IoTFleetWiseClient,
  ResourceNotFoundException,
} from "@aws-sdk/client-iotfleetwise";
import { listFleetsForVehicle } from "../list-fleets-for-vehicles";

// Mock the AWS SDK clients
jest.mock("@aws-sdk/client-iotfleetwise");

describe("listFleetsForVehicle", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("should return a list of fleets for a vehicle", async () => {
    // Mock data
    const vehicleName = "vehicle-1";
    const mockFleets = ["fleet-1", "fleet-2"];

    // Setup mocks
    IoTFleetWiseClient.prototype.send = jest.fn().mockResolvedValue({
      fleets: mockFleets,
    });

    // Execute
    const result = await listFleetsForVehicle({ name: vehicleName });

    // Verify
    expect(result).toEqual({
      fleets: [
        { id: "fleet-1", name: "fleet-1" },
        { id: "fleet-2", name: "fleet-2" },
      ],
    });

    // Verify calls
    expect(IoTFleetWiseClient.prototype.send).toHaveBeenCalledTimes(1);
  });

  it("should throw VehicleNotFound when vehicle doesn't exist", async () => {
    // Mock data
    const vehicleName = "non-existent-vehicle";

    // Setup mocks
    IoTFleetWiseClient.prototype.send = jest.fn().mockRejectedValue(
      new ResourceNotFoundException({
        message: "Resource not found",
        $metadata: {},
        resourceId: "non-existent-vehicle",
        resourceType: "vehicle",
      }),
    );

    // Execute and verify
    await expect(listFleetsForVehicle({ name: vehicleName })).rejects.toThrow(
      VehicleNotFound,
    );

    // Verify calls
    expect(IoTFleetWiseClient.prototype.send).toHaveBeenCalledTimes(1);
  });

  it("should handle empty fleets list", async () => {
    // Mock empty response
    IoTFleetWiseClient.prototype.send = jest.fn().mockResolvedValue({
      fleets: [],
    });

    // Execute
    const result = await listFleetsForVehicle({
      name: "vehicle-with-no-fleets",
    });

    // Verify
    expect(result).toEqual({ fleets: [] });
    expect(IoTFleetWiseClient.prototype.send).toHaveBeenCalledTimes(1);
  });

  it("should propagate other errors", async () => {
    // Mock error
    const mockError = new Error("Network error");
    IoTFleetWiseClient.prototype.send = jest.fn().mockRejectedValue(mockError);

    // Execute and verify
    await expect(listFleetsForVehicle({ name: "vehicle-1" })).rejects.toThrow(
      "Network error",
    );

    // Verify calls
    expect(IoTFleetWiseClient.prototype.send).toHaveBeenCalledTimes(1);
  });
});
