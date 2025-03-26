// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import { useState } from "react";
import { Button } from "@cloudscape-design/components";
import { Marker, Popup } from "react-map-gl/maplibre";
import { useSpring, animated } from "react-spring";
import VehicleIcon from "./VehicleIcon";
import styles from "./Devices.module.css";

export const VEHICLE_ICON_SIZE = 24;

const AnimatedMarker = animated(Marker); // This creates an animated version of the Marker

// Display single device with popup if clicked
const SingleDevice = ({
  device,
  selectedDevice,
  onChangeSelectedDevice,
}: any) => {
  const lastReportedTime = new Date(device.current.timestamp).toLocaleString();

  const { latitude, longitude } = useSpring({
    latitude: device.current.latitude,
    longitude: device.current.longitude,
    config: { tension: 280, friction: 280, mass: 50 },
  });

  return (
    <>
      <AnimatedMarker
        latitude={latitude}
        longitude={longitude}
        onClick={(e: any) => {
          e.originalEvent.stopPropagation();
          onChangeSelectedDevice(device.id);
        }}
        className={styles.marker}
      >
        <VehicleIcon size={VEHICLE_ICON_SIZE} />
      </AnimatedMarker>
    </>
  );
};

// Display tracked devices on map
const Devices = ({
  devices,
  onViewDeviceHistory,
}: {
  devices: any[];
  onViewDeviceHistory: any | undefined;
}) => {
  const [selectedDevice, setSelectedDevice] = useState();

  return (
    <>
      {devices?.length > 0 &&
        devices.map((device) => {
          return (
            <SingleDevice
              key={device.id}
              device={device}
              selectedDevice={selectedDevice === device.id}
              onChangeSelectedDevice={(device: any) =>
                setSelectedDevice(device)
              }
              onViewDeviceHistory={onViewDeviceHistory}
            />
          );
        })}
    </>
  );
};

export default Devices;
