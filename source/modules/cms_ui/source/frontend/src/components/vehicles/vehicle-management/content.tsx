// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { useContext, useEffect, useRef, useState } from "react";

import useNotifications from "./use-notifications";
import { UI_ROUTES } from "@/utils/constants";
import { joinRoutes } from "@/utils/path";
import { VehicleManagementContext } from "./VehicleManagementContext";
import { VehiclesPage } from "./components/VehiclesPage";
import { DeleteModal } from "./components/DeleteModal";
import VehicleDashboardView from "./components/vehicle-dashboard/VehicleDashboardView";
import { StatusIndicator } from "@cloudscape-design/components";
import { ApiContext } from "@/api/provider";
import {
  DeleteVehicleCommand,
  GetVehicleCommand,
  ListVehiclesCommand,
  VehicleItem,
} from "@com.cms.fleetmanagement/api-client";
import { useLocation, useNavigate } from "react-router-dom";

export function Content() {
  const [vehicles, setVehicles] = useState<Array<VehicleItem>>([]);
  const [selectedItems, setSelectedItems] = useState<Array<any>>([]);
  const [showDeleteModal, setShowDeleteModal] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<any>(null);
  const [locationVehicle, setLocationVehicle] = useState<
    VehicleItem | undefined
  >(undefined);
  const vmc = useContext(VehicleManagementContext);

  const api = useContext(ApiContext);
  const navigate = useNavigate();

  const location = useLocation();

  async function fetchVehicles(): Promise<VehicleItem[]> {
    const cmd = new ListVehiclesCommand();
    const output = await api.client.send(cmd);
    return output.vehicles || [];
  }

  useEffect(() => {
    async function setLocationVehicleAsync(locationVehicleId: string) {
      if (!locationVehicleId) {
        vmc.vehicle.setLocationVehicle(undefined);
        return;
      }

      //first check if we already have the vehicle available in memory
      setLocationVehicle(vehicles.find((it) => it.name === locationVehicleId));

      //if not, next try to fetch it
      if (!locationVehicle) {
        const cmd = new GetVehicleCommand({ name: locationVehicleId });
        const vehicle = await api.client.send(cmd);
        if (vehicle) {
          setLocationVehicle(vehicle);
        }
      }

      vmc.vehicle.setLocationVehicle(locationVehicle);
    }

    const locationVehicleId = window.location.hash.substring(1);

    const breadcrumbItems = [
      { text: "Vehicles", href: UI_ROUTES.VEHICLE_MANAGEMENT },
    ];

    if (window.location.hash.length > 0)
      breadcrumbItems.push({
        text: locationVehicleId,
        href: joinRoutes(UI_ROUTES.VEHICLE_MANAGEMENT, locationVehicleId),
      });

    vmc.breadcrumbs.setBreadcrumbItems(breadcrumbItems);

    setLocationVehicleAsync(locationVehicleId);
  }, [window.location.hash, locationVehicle]);

  const { notifications, notify } = useNotifications();

  useEffect(() => {
    // Check if there's a notification in the location state
    if (location.state?.notification) {
      notify([
        {
          id: location.state.notification.id,
          action: "create",
          status: location.state?.notification.status,
          message:
            location.state?.notification.status === "success"
              ? `Successfully created vehicle ${location.state.notification.id}.`
              : `Failed to create vehicle ${location.state.notification.id}.`,
        },
      ]);
      navigate(UI_ROUTES.VEHICLE_MANAGEMENT, { state: null });
    }
  }, [location]);

  const onDeleteInit = () => setShowDeleteModal(true);
  const onDeleteDiscard = () => setShowDeleteModal(false);
  const onDeleteConfirm = async () => {
    const vehiclesToDelete: VehicleItem[] = locationVehicle
      ? [locationVehicle]
      : selectedItems;
    setSelectedItems([]);
    setShowDeleteModal(false);

    const vehiclesDeletePromises = vehiclesToDelete.map(async (vehicle) => {
      notify([
        {
          id: vehicle.name,
          action: "delete",
          status: "in-progress",
          message: `Deleting vehicle ${vehicle.name}`,
        },
      ]);
      try {
        const cmd = new DeleteVehicleCommand({ name: vehicle.name });
        const response = await api.client.send(cmd);
        if (response.$metadata.httpStatusCode == 200) {
          notify([
            {
              id: vehicle.name,
              action: "delete",
              status: "success",
              message: `Successfully deleted vehicle ${vehicle.name}`,
            },
          ]);
        } else {
          notify([
            {
              id: vehicle.name,
              action: "delete",
              status: "error",
              message: `Error deleting vehicle ${vehicle.name}`,
            },
          ]);
        }
      } catch (err) {
        notify([
          {
            id: vehicle.name,
            action: "delete",
            status: "error",
            message: `Error deleting vehicle ${vehicle.name}`,
          },
        ]);
        console.log(err);
      }
    });
    await Promise.all(vehiclesDeletePromises);
    const vehicles = await fetchVehicles();
    setVehicles(vehicles);
  };

  useEffect(() => {
    setIsLoading(true);
    setError(null);

    if (window.location.hash.length > 0 && locationVehicle) {
      setIsLoading(false);
      return;
    }

    async function getVehicles() {
      try {
        const vehicles = await fetchVehicles();
        setVehicles(vehicles);
      } catch (err) {
        setError(err);
      } finally {
        setShowDeleteModal(false);
        setIsLoading(false);
      }
    }

    getVehicles();
  }, [window.location.hash]);

  useEffect(() => {
    setSelectedItems([]);
  }, [window.location.hash]);

  return (
    <>
      {window.location.hash && !vmc.vehicle.locationVehicle ? (
        <StatusIndicator type="loading">Loading...</StatusIndicator>
      ) : vmc.vehicle.locationVehicle ? (
        <VehicleDashboardView />
      ) : (
        <VehiclesPage
          vehicles={vehicles}
          selectedItems={selectedItems}
          setSelectedItems={setSelectedItems}
          onDeleteInit={onDeleteInit}
          notifications={notifications}
          isLoading={isLoading}
          error={error}
        />
      )}
      <DeleteModal
        visible={showDeleteModal}
        onDiscard={onDeleteDiscard}
        onDelete={onDeleteConfirm}
        vehicles={
          vmc.vehicle.locationVehicle
            ? [vmc.vehicle.locationVehicle]
            : selectedItems
        }
      />
    </>
  );
}
