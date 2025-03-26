// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import { useEffect, useState } from "react";

// import Button from "@cloudscape-design/components/button";
// import TrackersPanel from "./TrackersPanel";
import Devices from "./Devices";

// import {
//   DEMO_POSITION_UPDATE_INTERVAL,
//   POSITION_UPDATES_TRUCK_1,
// } from "../../DemoData.js";

// Layer in the app that contains Trackers functionalities
const PositionLayer = ({ data }: any) => {
  const [devices, setDevices] = useState([data]);
  //   const fetchDevicePositions = async () => {
  //     const fetchedDevices = await callListDevicePositionsCommand(readOnlyLocationClient);
  //     const sorted = fetchedDevices.Entries.sort((a, b) => {
  //       return a.SampleTime < b.SampleTime ? 1 : -1;
  //     });
  //   };

  return (
    <>
      <Devices devices={devices} onViewDeviceHistory={undefined} />
    </>
  );
};

export default PositionLayer;
