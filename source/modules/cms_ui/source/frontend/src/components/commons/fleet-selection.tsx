// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { FormField, Select, SpaceBetween } from "@cloudscape-design/components";
import { useContext, useEffect, useState } from "react";
import { UserContext } from "./UserContext";
import {
  FleetItem,
  ListFleetsCommand,
} from "@com.cms.fleetmanagement/api-client";
import { ApiContext } from "@/api/provider";

type SelectContent = {
  label: string;
  value: string;
};

export function FleetSelectionItem() {
  const uc = useContext(UserContext);

  const [fleetsData, setFleetsData] = useState<FleetItem[]>([]);
  const [fleetSelections, setFleetSelections] = useState<SelectContent[]>([]);
  const [fleetDataStatus, setFleetDataStatus] = useState<
    "loading" | "finished" | "error"
  >("loading");

  const api = useContext(ApiContext);

  const fetchFleets = async () => {
    const cmd = new ListFleetsCommand();
    const output = await api.client.send(cmd);
    return output.fleets || [];
  };

  useEffect(() => {
    fetchFleets().then((fleets) => {
      setFleetsData(fleets);
      const selectionFleets = fleets.map((fleet) => {
        return {
          label: fleet.name,
          value: fleet.id,
        };
      });
      setFleetSelections(selectionFleets);
      setFleetDataStatus("finished");
      if (fleets.length > 0) {
        if (
          uc.fleet.selectedFleet == null ||
          (uc.fleet.selectedFleet != null &&
            !fleets.find((fleet) => fleet.id === uc.fleet.selectedFleet?.id))
        ) {
          uc.fleet.setSelectedFleet(fleetsData[0]);
        }
      } else {
        uc.fleet.resetSelectedFleet(null);
      }
    });
  }, []);

  return (
    <SpaceBetween size="xs" direction="horizontal" alignItems="center">
      <FormField label="Selected fleet:" />
      <Select
        loadingText="fetching fleets..."
        errorText="failed to fetch fleets"
        statusType={fleetDataStatus}
        selectedOption={
          uc.fleet.selectedFleet
            ? {
                label: uc.fleet.selectedFleet.name,
                value: uc.fleet.selectedFleet.id,
              }
            : null
        }
        onChange={({ detail }) =>
          uc.fleet.setSelectedFleet(
            fleetsData.find(
              (fleet) => fleet.id === detail.selectedOption.value,
            ) || null,
          )
        }
        options={fleetSelections}
      />
    </SpaceBetween>
  );
}
