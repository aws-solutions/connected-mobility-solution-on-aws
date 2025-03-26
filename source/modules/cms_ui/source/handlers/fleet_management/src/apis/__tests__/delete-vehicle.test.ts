// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { deleteVehicle } from "../delete-vehicle";
import { VehicleNotFound } from "@com.cms.fleetmanagement/api-server";
import {
  IoTFleetWiseClient,
  DeleteVehicleCommand,
  ResourceNotFoundException,
} from "@aws-sdk/client-iotfleetwise";
import { IoTClient, DeleteThingCommand } from "@aws-sdk/client-iot";

// Mock the AWS SDK
jest.mock("@aws-sdk/client-iotfleetwise");
jest.mock("@aws-sdk/client-iot");

describe("deleteVehicle", () => {
  // Reset mocks before each test
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("should delete a vehicle successfully", async () => {
    // Setup mock implementations
    const mockFleetwiseSend = jest.fn().mockResolvedValue({});
    (IoTFleetWiseClient as jest.Mock).mockImplementation(() => ({
      send: mockFleetwiseSend,
    }));

    const mockIoTSend = jest.fn().mockResolvedValue({});
    (IoTClient as jest.Mock).mockImplementation(() => ({
      send: mockIoTSend,
    }));

    // Call the function
    const result = await deleteVehicle({ name: "test-vehicle" });

    // Verify the results
    expect(result).toBeUndefined();

    // Verify FleetWise client was called correctly
    expect(IoTFleetWiseClient).toHaveBeenCalledTimes(1);
    expect(mockFleetwiseSend).toHaveBeenCalledTimes(1);
    expect(DeleteVehicleCommand).toHaveBeenCalledWith({
      vehicleName: "test-vehicle",
    });

    // Verify IoT client was called correctly
    expect(IoTClient).toHaveBeenCalledTimes(1);
    expect(mockIoTSend).toHaveBeenCalledTimes(1);
    expect(DeleteThingCommand).toHaveBeenCalledWith({
      thingName: "test-vehicle",
    });
  });

  it("should throw VehicleNotFound when vehicle doesn't exist", async () => {
    // Setup mock implementation to throw ResourceNotFoundException
    const mockFleetwiseSend = jest.fn().mockRejectedValue(
      new ResourceNotFoundException({
        message: "Resource not found",
        $metadata: {},
        resourceId: "non-existent-vehicle",
        resourceType: "Vehicle",
      }),
    );
    (IoTFleetWiseClient as jest.Mock).mockImplementation(() => ({
      send: mockFleetwiseSend,
    }));

    // IoT client mock (shouldn't be called in this case)
    const mockIoTSend = jest.fn().mockResolvedValue({});
    (IoTClient as jest.Mock).mockImplementation(() => ({
      send: mockIoTSend,
    }));

    // Call the function and expect it to throw
    await expect(
      deleteVehicle({ name: "non-existent-vehicle" }),
    ).rejects.toThrow(VehicleNotFound);

    // Verify the FleetWise mock was called
    expect(IoTFleetWiseClient).toHaveBeenCalledTimes(1);
    expect(mockFleetwiseSend).toHaveBeenCalledTimes(1);

    // Verify IoT client was not called
    expect(mockIoTSend).not.toHaveBeenCalled();
  });

  it("should propagate other errors", async () => {
    // Setup mock implementation to throw a different error
    const error = new Error("Some other error");
    const mockFleetwiseSend = jest.fn().mockRejectedValue(error);
    (IoTFleetWiseClient as jest.Mock).mockImplementation(() => ({
      send: mockFleetwiseSend,
    }));

    // Call the function and expect it to throw the original error
    await expect(deleteVehicle({ name: "test-vehicle" })).rejects.toThrow(
      "Some other error",
    );

    // Verify the mock was called
    expect(IoTFleetWiseClient).toHaveBeenCalledTimes(1);
    expect(mockFleetwiseSend).toHaveBeenCalledTimes(1);
  });
});
