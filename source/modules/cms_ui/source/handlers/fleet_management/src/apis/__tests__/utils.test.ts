// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { VehicleStatus } from "@com.cms.fleetmanagement/api-server";
import { IoTClient, ListThingPrincipalsCommand } from "@aws-sdk/client-iot";
import { getVehicleStatus } from "../utils";

// Mock the AWS SDK
jest.mock("@aws-sdk/client-iot");

describe("Vehicle Status Utils", () => {
  const mockSend = jest.fn();
  const mockIoTClient = IoTClient as jest.MockedClass<typeof IoTClient>;

  beforeEach(() => {
    jest.clearAllMocks();
    mockIoTClient.prototype.send = mockSend;
  });

  it("should return ACTIVE status when vehicle has principals", async () => {
    // Arrange
    const vehicleName = "test-vehicle";
    mockSend.mockResolvedValueOnce({
      principals: ["principal1", "principal2"],
    });

    // Act
    const result = await getVehicleStatus(vehicleName);

    // Assert
    expect(ListThingPrincipalsCommand).toHaveBeenCalledWith({
      thingName: vehicleName,
    });
    expect(mockSend).toHaveBeenCalledTimes(1);
    expect(result).toBe(VehicleStatus.ACTIVE);
  });

  it("should return INACTIVE status when vehicle has no principals", async () => {
    // Arrange
    const vehicleName = "test-vehicle-inactive";
    mockSend.mockResolvedValueOnce({
      principals: [],
    });

    // Act
    const result = await getVehicleStatus(vehicleName);

    // Assert
    expect(ListThingPrincipalsCommand).toHaveBeenCalledWith({
      thingName: vehicleName,
    });
    expect(mockSend).toHaveBeenCalledTimes(1);
    expect(result).toBe(VehicleStatus.INACTIVE);
  });

  it("should handle errors from IoT client", async () => {
    // Arrange
    const vehicleName = "test-vehicle-error";
    const error = new Error("IoT client error");
    mockSend.mockRejectedValueOnce(error);

    // Act & Assert
    await expect(getVehicleStatus(vehicleName)).rejects.toThrow(
      "IoT client error",
    );
    expect(ListThingPrincipalsCommand).toHaveBeenCalledWith({
      thingName: vehicleName,
    });
    expect(mockSend).toHaveBeenCalledTimes(1);
  });
});
