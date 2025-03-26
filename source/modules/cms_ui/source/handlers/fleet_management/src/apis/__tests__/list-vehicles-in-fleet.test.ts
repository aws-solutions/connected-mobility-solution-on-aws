// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { VehicleStatus } from "@com.cms.fleetmanagement/api-server";
import { IoTFleetWiseClient } from "@aws-sdk/client-iotfleetwise";
import { listVehiclesInFleet } from "../list-vehicles-in-fleet";
import { getVehicleStatus } from "../utils";

// Mock the AWS SDK clients
jest.mock("@aws-sdk/client-iotfleetwise");
jest.mock("../utils");

describe("listVehiclesInFleet", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("should return a list of vehicles in a fleet with their details", async () => {
    // Mock data
    const fleetId = "fleet-1";
    const mockVehicles = ["vehicle-1", "vehicle-2"];
    const mockVehicleDetails = [
      {
        vehicleName: "vehicle-1",
        attributes: {
          make: "Toyota",
          model: "Camry",
          year: "2020",
          license: "ABC123",
        },
      },
      {
        vehicleName: "vehicle-2",
        attributes: {
          make: "Honda",
          model: "Civic",
          year: "2021",
          license: "XYZ789",
        },
      },
    ];

    // Setup mocks
    const mockSend = jest
      .fn()
      .mockImplementationOnce(() => Promise.resolve({ vehicles: mockVehicles }))
      .mockImplementationOnce(() => Promise.resolve(mockVehicleDetails[0]))
      .mockImplementationOnce(() => Promise.resolve(mockVehicleDetails[1]));

    IoTFleetWiseClient.prototype.send = mockSend;

    (getVehicleStatus as jest.Mock).mockImplementation((vehicleName) => {
      if (vehicleName === "vehicle-1") {
        return Promise.resolve(VehicleStatus.ACTIVE);
      } else {
        return Promise.resolve(VehicleStatus.INACTIVE);
      }
    });

    // Execute
    const result = await listVehiclesInFleet({ id: fleetId });

    // Verify
    expect(result).toEqual({
      vehicles: [
        {
          name: "vehicle-1",
          status: VehicleStatus.ACTIVE,
          attributes: {
            make: "Toyota",
            model: "Camry",
            year: 2020,
            licensePlate: "ABC123",
          },
        },
        {
          name: "vehicle-2",
          status: VehicleStatus.INACTIVE,
          attributes: {
            make: "Honda",
            model: "Civic",
            year: 2021,
            licensePlate: "XYZ789",
          },
        },
      ],
    });

    // Verify calls
    expect(IoTFleetWiseClient.prototype.send).toHaveBeenCalledTimes(3);
    expect(getVehicleStatus).toHaveBeenCalledWith("vehicle-1");
    expect(getVehicleStatus).toHaveBeenCalledWith("vehicle-2");
  });

  it("should handle empty vehicle list in fleet", async () => {
    // Mock empty response
    IoTFleetWiseClient.prototype.send = jest.fn().mockResolvedValue({
      vehicles: [],
    });

    // Execute
    const result = await listVehiclesInFleet({ id: "empty-fleet" });

    // Verify
    expect(result).toEqual({ vehicles: [] });
    expect(IoTFleetWiseClient.prototype.send).toHaveBeenCalledTimes(1);
    expect(getVehicleStatus).not.toHaveBeenCalled();
  });
});
