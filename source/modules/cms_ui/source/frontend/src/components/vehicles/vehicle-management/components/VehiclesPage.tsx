// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { AppLayout, Flashbar } from "@cloudscape-design/components";
import VehiclesTable from "./vehicles-table";
import { Navigation } from "@/components/commons";
import { UI_ROUTES } from "@/utils/constants";

export function VehiclesPage({
  vehicles,
  selectedItems,
  setSelectedItems,
  onDeleteInit,
  notifications,
  isLoading,
  error,
}: any) {
  return (
    <AppLayout
      content={
        <VehiclesTable
          vehicles={vehicles}
          selectedItems={selectedItems}
          onSelectionChange={(event: any) =>
            setSelectedItems(event.detail.selectedItems)
          }
          onDelete={onDeleteInit}
          isLoading={isLoading}
          error={error}
        />
      }
      notifications={<Flashbar items={notifications} stackItems={true} />}
      navigation={<Navigation activeHref={UI_ROUTES.VEHICLE_MANAGEMENT} />}
      navigationOpen={false}
      navigationHide={true}
      toolsHide={true}
      contentType="table"
    />
  );
}
