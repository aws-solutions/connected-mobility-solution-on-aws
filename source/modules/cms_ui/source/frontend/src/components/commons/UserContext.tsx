// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { useLocalStorage } from "@/components/commons/use-local-storage";
import { FleetItem } from "@com.cms.fleetmanagement/api-client";
import { applyMode, Mode } from "@cloudscape-design/global-styles";
import { VehicleItem } from "@com.cms.fleetmanagement/api-client";
import { createContext, useEffect, useMemo, useState } from "react";

export const isVisualRefresh = true;
const themeLocalStorageKey = "Awsui-Theme-Preference";

type FleetContextType = {
  selectedFleet: FleetItem | null;
  setSelectedFleet: (fleet: FleetItem | null) => void;
  resetSelectedFleet: (fleet: FleetItem | null) => void;
};

type VehicleContextType = {
  selectedVehicle: VehicleItem | null;
  setSelectedVehicle: (vehicle: VehicleItem | null) => void;
  resetSelectedVehicle: (vehicle: VehicleItem | null) => void;
  fleetForSelectedVehicle: FleetItem | null;
  setFleetForSelectedVehicle: (fleet: FleetItem | null) => void;
};

type ThemeContextType = {
  currentThemeMode: Mode;
  switchThemeMode: () => void;
  applyInitialTheme: () => void;
};

type DemoModeType = {
  isDemoMode: boolean;
  setIsDemoMode: (isDemoMode: boolean) => void;
};

type UserContextType = {
  fleet: FleetContextType;
  vehicle: VehicleContextType;
  theme: ThemeContextType;
  demoMode: DemoModeType;
};

const DEFAULT_CONTEXT = {
  fleet: {
    selectedFleet: null,
    setSelectedFleet: () => {},
    resetSelectedFleet: () => {},
  },
  vehicle: {
    selectedVehicle: null,
    setSelectedVehicle: () => {},
    resetSelectedVehicle: () => {},
    fleetForSelectedVehicle: null,
    setFleetForSelectedVehicle: () => {},
  },
  theme: {
    currentThemeMode: Mode.Light,
    switchThemeMode: () => {},
    applyInitialTheme: () => {},
  },
  demoMode: {
    isDemoMode: false,
    setIsDemoMode: () => {},
  },
};

export const UserContext = createContext<UserContextType>(DEFAULT_CONTEXT);

export const UserContextProvider = ({
  children,
}: {
  children: React.ReactNode;
}) => {
  const [selectedFleet, setSelectedFleet, resetSelectedFleet] =
    useLocalStorage<FleetItem | null>("UserContext_selectedFleet", null);

  const [selectedVehicle, setSelectedVehicle, resetSelectedVehicle] =
    useLocalStorage<VehicleItem | null>("UserContext_selectedVehicle", null);

  const [
    fleetForSelectedVehicle,
    setFleetForSelectedVehicle,
    resetFleetForSelectedVehicle,
  ] = useLocalStorage<FleetItem | null>(
    "UserContext_fleetForSelectedVehicle",
    null,
  );

  const fleet = {
    selectedFleet: selectedFleet,
    setSelectedFleet: setSelectedFleet,
    resetSelectedFleet: resetSelectedFleet,
  };

  const vehicle = {
    selectedVehicle: selectedVehicle,
    fleetForSelectedVehicle: fleetForSelectedVehicle,
    setFleetForSelectedVehicle: setFleetForSelectedVehicle,
    setSelectedVehicle: setSelectedVehicle,
    resetSelectedVehicle: resetSelectedVehicle,
  };

  const [currentThemeMode, setCurrentThemeMode, _] = useLocalStorage<Mode>(
    themeLocalStorageKey,
    Mode.Light,
  );

  const [isDemoMode, setIsDemoMode] = useState(false);

  function updateThemeMode(themeMode: Mode) {
    applyMode(themeMode);
    setCurrentThemeMode(themeMode);
  }

  function switchThemeMode() {
    if (currentThemeMode === Mode.Light) {
      updateThemeMode(Mode.Dark);
    } else {
      updateThemeMode(Mode.Light);
    }
  }

  const theme = {
    currentThemeMode: currentThemeMode,
    switchThemeMode: switchThemeMode,
    applyInitialTheme: () => applyMode(currentThemeMode as Mode),
  };

  const demoMode = {
    isDemoMode: isDemoMode,
    setIsDemoMode: setIsDemoMode,
  };

  const contextValue = useMemo(
    () => ({
      fleet,
      vehicle,
      theme,
      demoMode,
    }),
    [fleet, vehicle],
  );

  return (
    <UserContext.Provider value={contextValue}>{children}</UserContext.Provider>
  );
};
