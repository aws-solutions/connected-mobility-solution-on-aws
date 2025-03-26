// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

export interface Coordinate {
  latitude: number;
  longitude: number;
}

export interface VehicleRouteFile {
  vehicleIndex: number;
  warehouse: Coordinate;
  // stops: Coordinate[];
  recordedEvents: RecordedEvent[];
  data: {
    routes: {
      geometry: {
        coordinates: [number, number][];
      };
    }[];
  };
}

export interface VehicleRoute {
  routeCoordinates: Coordinate[];
  traveledPath: Coordinate[];
  vehiclePosition: Coordinate;
  currentIndex: number;
  stepIndex: number;
  warehouse: Coordinate;
}
export interface Vehicle {
  route: VehicleRoute;
  recordedEvents: RecordedEvent[];
  details: string;
  driverId: string;
  vehicleId: string;
  startTime: number;
  status: VEHICLE_STATUS;
}

export interface RecordedEvent {
  latitude: number;
  longitude: number;
  title: string;
  timestamp: number;
}

export interface DriverDetails {
  name: string;
  score: number;
  photo: string;
}

export interface VehicleDetails {
  metrics: any[];
  status: VEHICLE_STATUS;
}

export interface DetailedVehicleInfo {
  vehicle: Vehicle;
  vehicleDetails: VehicleDetails;
  driverDetails: DriverDetails;
  filteredRecordedEvents: RecordedEvent[];
}

export enum VEHICLE_STATUS {
  HEALTHY = "HEALTHY",
  UNHEALTHY = "UNHEALTHY",
  UNKNOWN = "UNKNOWN",
}
