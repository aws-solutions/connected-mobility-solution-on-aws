// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { AppLayout, Flashbar } from "@cloudscape-design/components";
import CampaignsTable from "./campaigns-table";
import { Navigation } from "@/components/commons";
import { UI_ROUTES } from "@/utils/constants";

export function CampaignsPage({
  campaigns,
  selectedItems,
  setSelectedItems,
  onEditInit,
  onDeleteInit,
  notifications,
  isLoading,
  error,
}: any) {
  return (
    <AppLayout
      content={
        <CampaignsTable
          campaigns={campaigns}
          selectedItems={selectedItems}
          onSelectionChange={(event: any) =>
            setSelectedItems(event.detail.selectedItems)
          }
          onDelete={onDeleteInit}
          onEdit={onEditInit}
          isLoading={isLoading}
          error={error}
        />
      }
      notifications={<Flashbar items={notifications} stackItems={true} />}
      navigation={<Navigation activeHref={UI_ROUTES.CAMPAIGN_MANAGEMENT} />}
      navigationOpen={false}
      navigationHide={true}
      toolsHide={true}
      contentType="table"
    />
  );
}
