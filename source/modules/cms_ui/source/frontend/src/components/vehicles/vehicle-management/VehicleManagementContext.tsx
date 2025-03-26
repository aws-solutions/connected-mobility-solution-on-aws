// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { VehicleItem } from "@com.cms.fleetmanagement/api-client";
import { BreadcrumbGroupProps } from "@cloudscape-design/components";
import { createContext, useMemo, useState } from "react";

type BreadcrumbContextType = {
  breadcrumbItems: BreadcrumbGroupProps["items"];
  setBreadcrumbItems: (items: BreadcrumbGroupProps["items"]) => void;
};

type VehicleContextType = {
  locationVehicle: VehicleItem | undefined;
  setLocationVehicle: (vehicle: VehicleItem | undefined) => void;
};

type VehicleManagementContextType = {
  breadcrumbs: BreadcrumbContextType;
  vehicle: VehicleContextType;
};

const DEFAULT_CONTEXT: VehicleManagementContextType = {
  breadcrumbs: {
    breadcrumbItems: [],
    setBreadcrumbItems: () => {},
  },
  vehicle: {
    locationVehicle: undefined,
    setLocationVehicle: () => {},
  },
};

export const VehicleManagementContext =
  createContext<VehicleManagementContextType>(DEFAULT_CONTEXT);

export const VehicleManagementContextProvider = ({
  children,
}: {
  children: React.ReactNode;
}) => {
  const [breadcrumbItems, setBreadcrumbItems] = useState<
    BreadcrumbGroupProps["items"]
  >([]);

  const breadcrumbs = {
    breadcrumbItems: breadcrumbItems,
    setBreadcrumbItems: setBreadcrumbItems,
  };

  const [locationVehicle, setLocationVehicle] = useState<
    VehicleItem | undefined
  >(undefined);

  const vehicle = {
    locationVehicle: locationVehicle,
    setLocationVehicle: setLocationVehicle,
  };

  const contextValue = useMemo(
    () => ({
      breadcrumbs: breadcrumbs,
      vehicle: vehicle,
    }),
    [breadcrumbs, vehicle],
  );

  return (
    <VehicleManagementContext.Provider value={contextValue}>
      {children}
    </VehicleManagementContext.Provider>
  );
};
