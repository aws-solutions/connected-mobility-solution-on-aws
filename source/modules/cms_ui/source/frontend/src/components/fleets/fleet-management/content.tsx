// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { useContext, useEffect, useRef, useState } from "react";
import useNotifications from "./use-notifications";
import { UI_ROUTES } from "@/utils/constants";
import { joinRoutes } from "@/utils/path";
import { FleetManagementContext } from "./FleetManagementContext";
import { FleetDetailsPage } from "./components/FleetDetailsPage";
import { FleetsPage } from "./components/FleetsPage";
import { DeleteModal } from "./components/DeleteModal";
import { StatusIndicator } from "@cloudscape-design/components";
import { ApiContext } from "@/api/provider";
import {
  ListFleetsCommand,
  FleetItem,
  GetFleetCommand,
  DeleteFleetCommand,
} from "@com.cms.fleetmanagement/api-client";
import { useNavigate } from "react-router-dom";

export function Content() {
  const [fleets, setFleets] = useState<Array<FleetItem>>([]);
  const [selectedItems, setSelectedItems] = useState<Array<any>>([]);
  const [showDeleteModal, setShowDeleteModal] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<any>(null);
  const fmc = useContext(FleetManagementContext);

  const [locationFleet, setLocationFleet] = useState<any>(undefined);

  const api = useContext(ApiContext);

  const navigate = useNavigate();

  const fetchFleets = async () => {
    const cmd = new ListFleetsCommand();
    const output = await api.client.send(cmd);
    setFleets(output.fleets || []);
  };

  const fetchFleet = async (fleetId: string) => {
    const input = { id: fleetId };
    const cmd = new GetFleetCommand(input);
    const output = await api.client.send(cmd);
    return output;
  };

  useEffect(() => {
    async function setLocationFleetAsync() {
      const locationFleetId = window.location.hash.substring(1);

      if (!locationFleetId) {
        setLocationFleet(undefined);
        return;
      }

      //first check if we already have the fleet available in memory
      let newLocationFleet = fleets.find((it) => it.id === locationFleetId);

      //if not, next try to fetch it
      if (!newLocationFleet) {
        const fleet = await fetchFleet(locationFleetId);
        if (fleet != undefined) {
          newLocationFleet = fleet;
        }
      }

      setLocationFleet(newLocationFleet);

      const breadcrumbItems = [
        { text: "Fleets", href: UI_ROUTES.FLEET_MANAGEMENT },
      ];

      if (newLocationFleet && newLocationFleet.id)
        breadcrumbItems.push({
          text: newLocationFleet.id,
          href: joinRoutes(UI_ROUTES.FLEET_MANAGEMENT, newLocationFleet.id),
        });

      fmc.breadcrumbs.setBreadcrumbItems(breadcrumbItems);
    }

    setLocationFleetAsync();
  }, [window.location.hash]);

  const { notifications, notify } = useNotifications();

  const onDeleteInit = () => setShowDeleteModal(true);
  const onEditInit = () => {
    navigate(`${UI_ROUTES.FLEET_EDIT}#${selectedItems[0].id}`);
  };
  const onDeleteDiscard = () => {
    setShowDeleteModal(false);
  };
  const onDeleteConfirm = async () => {
    const fleetsToDelete: FleetItem[] = locationFleet
      ? [locationFleet]
      : selectedItems;
    setSelectedItems([]);
    setShowDeleteModal(false);

    const fleetsDeletePromises = fleetsToDelete.map(async (fleet) => {
      notify([
        {
          id: fleet.id,
          action: "delete",
          status: "in-progress",
          message: `Deleting fleet ${fleet.id}`,
        },
      ]);
      try {
        const cmd = new DeleteFleetCommand({ id: fleet.id });
        const response = await api.client.send(cmd);
        if (response.$metadata.httpStatusCode == 200) {
          notify([
            {
              id: fleet.id,
              action: "delete",
              status: "success",
              message: `Successfully deleted fleet ${fleet.id}`,
            },
          ]);
        } else {
          notify([
            {
              id: fleet.id,
              action: "delete",
              status: "error",
              message: `Error deleting fleet ${fleet.id}`,
            },
          ]);
        }
      } catch (err) {
        notify([
          {
            id: fleet.id,
            action: "delete",
            status: "error",
            message: `Error deleting fleet ${fleet.id}`,
          },
        ]);
        console.log(err);
      }
    });
    await Promise.all(fleetsDeletePromises);
    fetchFleets();
  };

  useEffect(() => {
    setIsLoading(true);
    setError(null);
    if (window.location.hash.length > 0) {
      setIsLoading(false);
      return;
    }

    async function getFleetsSummary() {
      try {
        await fetchFleets();
      } catch (err) {
        setError(err);
      } finally {
        setShowDeleteModal(false);
        setIsLoading(false);
      }
    }
    getFleetsSummary();
  }, [window.location.hash]);

  return (
    <>
      {window.location.hash && !locationFleet ? (
        <StatusIndicator type="loading">Loading...</StatusIndicator>
      ) : locationFleet ? (
        <FleetDetailsPage
          fleetId={locationFleet.id}
          onDeleteInit={onDeleteInit}
          notifications={notifications}
        />
      ) : (
        <FleetsPage
          fleets={fleets}
          selectedItems={selectedItems}
          setSelectedItems={setSelectedItems}
          onEditInit={onEditInit}
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
        fleets={locationFleet ? [locationFleet] : selectedItems}
      />
    </>
  );
}
