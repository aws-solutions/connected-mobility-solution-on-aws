// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

// cards-config.tsx

import React from "react";
import { CardsProps } from "@cloudscape-design/components/cards";
import { DetailedVehicleInfo, VEHICLE_STATUS } from "../interfaces";
import { StatusIndicator } from "@cloudscape-design/components";

const vehicleStatusIndicator = (
  vehicle: DetailedVehicleInfo["vehicleDetails"],
) => {
  switch (vehicle.status) {
    case VEHICLE_STATUS.UNHEALTHY:
      return <StatusIndicator type="error">{vehicle.status}</StatusIndicator>;
    case VEHICLE_STATUS.HEALTHY:
      return <StatusIndicator type="success">{vehicle.status}</StatusIndicator>;
    default:
      return <StatusIndicator type="warning">Unknown</StatusIndicator>;
  }
};

export const CARD_DEFINITIONS: CardsProps.CardDefinition<DetailedVehicleInfo> =
  {
    header: (vehicleInfo) => (
      <div>
        <a
          style={{
            fontSize: "1.25em",
            textDecoration: "none",
            color: "inherit",
          }}
        >
          {vehicleInfo.vehicle.vehicleId}
        </a>
      </div>
    ),
    sections: [
      {
        id: "driver",
        header: "Driver",
        width: 50,
        content: (vehicleInfo) => vehicleInfo.driverDetails.name,
      },
      {
        id: "driverScore",
        header: "Driver Score",
        width: 50,
        content: (vehicleInfo) => vehicleInfo.driverDetails.score,
      },
      {
        id: "location",
        header: "Location",
        width: 50,
        content: (vehicleInfo) => (
          <div>
            <div>
              Latitude: {vehicleInfo.vehicle.route.vehiclePosition.latitude}
            </div>
            <div>
              Longitude: {vehicleInfo.vehicle.route.vehiclePosition.longitude}
            </div>
          </div>
        ),
      },
      {
        id: "status",
        header: "Status",
        width: 50,
        content: (vehicleInfo) =>
          vehicleStatusIndicator(vehicleInfo.vehicleDetails),
      },
    ],
  };

export const CARD_DEFINITION_SELECTED: CardsProps.CardDefinition<DetailedVehicleInfo> =
  {
    header: (detailedVehicle) =>
      `Selected Vehicle: ${detailedVehicle.vehicle.vehicleId}`,
    sections: [
      {
        id: "locations",
        header: "Locations",
        content: (detailedVehicle) => (
          <div>
            <div>Current Location:</div>
            <div>
              {`${detailedVehicle.vehicle.route.vehiclePosition.latitude}, ${detailedVehicle.vehicle.route.vehiclePosition.longitude}`}
            </div>
            <div>Warehouse Location:</div>
            <div>
              {`${detailedVehicle.vehicle.route.warehouse.latitude}, ${detailedVehicle.vehicle.route.warehouse.longitude}`}
            </div>
          </div>
        ),
      },
      {
        id: "status",
        header: "Status",
        width: 50,
        content: (detailedVehicle) =>
          vehicleStatusIndicator(detailedVehicle.vehicleDetails),
      },
      {
        id: "metrics",
        header: "Metrics",
        width: 100,
        content: (detailedVehicle) => {
          const metrics = detailedVehicle.vehicleDetails.metrics || [];
          return (
            <ul style={{ margin: 0, paddingLeft: "1.5rem" }}>
              {metrics.map((metric, idx) => (
                <li key={idx}>
                  {metric.name}: {metric.value}
                </li>
              ))}
            </ul>
          );
        },
      },
      {
        id: "recordedEvents",
        header: "Recorded Events",
        content: (detailedVehicle) => {
          const events = detailedVehicle.filteredRecordedEvents || [];
          if (events.length === 0) {
            return <div>No recorded events.</div>;
          }
          return (
            <ul style={{ margin: 0, paddingLeft: "1.5rem" }}>
              {events.map((event, idx) => (
                <li key={idx}>
                  {event.title} event recorded at{" "}
                  {new Date(
                    detailedVehicle.vehicle.startTime + event.timestamp,
                  ).toLocaleString("en-US")}
                </li>
              ))}
            </ul>
          );
        },
      },
    ],
  };
