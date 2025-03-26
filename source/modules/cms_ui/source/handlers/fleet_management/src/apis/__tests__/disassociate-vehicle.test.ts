// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { disassociateVehicle } from "../disassociate-vehicle";
import { VehicleNotFound } from "@com.cms.fleetmanagement/api-server";
import {
  IoTFleetWiseClient,
  DisassociateVehicleFleetCommand,
  ResourceNotFoundException,
} from "@aws-sdk/client-iotfleetwise";

// Mock the AWS SDK
jest.mock("@aws-sdk/client-iotfleetwise");

describe("disassociateVehicle", () => {
  const mockSend = jest.fn();
  const mockIoTFleetWiseClient = IoTFleetWiseClient as jest.MockedClass<
    typeof IoTFleetWiseClient
  >;

  beforeEach(() => {
    jest.clearAllMocks();
    mockIoTFleetWiseClient.prototype.send = mockSend;
  });

  it("should successfully disassociate a vehicle from a fleet", async () => {
    // Arrange
    const input = {
      name: "test-vehicle",
      fleetId: "test-fleet",
    };
    mockSend.mockResolvedValueOnce({});

    // Act
    const result = await disassociateVehicle(input);

    // Assert
    expect(mockSend).toHaveBeenCalledTimes(1);
    expect(mockIoTFleetWiseClient).toHaveBeenCalledTimes(1);
    expect(DisassociateVehicleFleetCommand).toHaveBeenCalledWith({
      vehicleName: input.name,
      fleetId: input.fleetId,
    });
    expect(result).toBeUndefined();
  });

  it("should throw VehicleNotFound when vehicle or fleet doesn't exist", async () => {
    // Arrange
    const input = {
      name: "non-existent-vehicle",
      fleetId: "non-existent-fleet",
    };
    const error = new ResourceNotFoundException({
      message: "Resource not found",
      $metadata: {},
      resourceId: "non-existent-vehicle",
      resourceType: "vehicle",
    });
    mockSend.mockRejectedValueOnce(error);

    // Act & Assert
    await expect(disassociateVehicle(input)).rejects.toThrow(VehicleNotFound);
    expect(mockSend).toHaveBeenCalledTimes(1);
  });

  it("should propagate other errors", async () => {
    // Arrange
    const input = {
      name: "test-vehicle",
      fleetId: "test-fleet",
    };
    const error = new Error("Some other error");
    mockSend.mockRejectedValueOnce(error);

    // Act & Assert
    await expect(disassociateVehicle(input)).rejects.toThrow(
      "Some other error",
    );
    expect(mockSend).toHaveBeenCalledTimes(1);
  });
});
