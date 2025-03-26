// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { useContext, useEffect, useState } from "react";
import useNotifications from "./use-notifications";
import { UI_ROUTES } from "@/utils/constants";
import { joinRoutes } from "@/utils/path";
import { CampaignManagementContext } from "./CampaignManagementContext";
import { CampaignDetailsPage } from "./components/CampaignDetailsPage";
import { CampaignsPage } from "./components/CampaignsPage";
import { DeleteModal } from "./components/DeleteModal";
import { StatusIndicator } from "@cloudscape-design/components";
import { ApiContext } from "@/api/provider";
import {
  ListCampaignsCommand,
  GetCampaignCommand,
  DeleteCampaignCommand,
  CampaignItem,
} from "@com.cms.fleetmanagement/api-client";
import { useNavigate } from "react-router-dom";

export function Content() {
  const [campaigns, setCampaigns] = useState<Array<CampaignItem>>([]);
  const [selectedItems, setSelectedItems] = useState<Array<any>>([]);
  const [showDeleteModal, setShowDeleteModal] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<any>(null);
  const cmc = useContext(CampaignManagementContext);

  const [locationCampaign, setLocationCampaign] = useState<any>(undefined);

  const api = useContext(ApiContext);

  const navigate = useNavigate();

  const fetchCampaigns = async () => {
    const cmd = new ListCampaignsCommand();
    const output = await api.client.send(cmd);
    setCampaigns(output.campaigns || []);
  };

  const fetchCampaign = async (campaignName: string) => {
    const input = { name: campaignName };
    const cmd = new GetCampaignCommand(input);
    const output = await api.client.send(cmd);
    return output;
  };

  useEffect(() => {
    async function setLocationCampaignAsync() {
      const locationCampaignName = window.location.hash.substring(1);

      if (!locationCampaignName) {
        setLocationCampaign(undefined);
        return;
      }

      //first check if we already have the campaign available in memory
      let newLocationCampaign = campaigns.find(
        (it) => it.name === locationCampaignName,
      );

      //if not, next try to fetch it
      if (!newLocationCampaign) {
        const campaign = await fetchCampaign(locationCampaignName);
        if (campaign != undefined) {
          newLocationCampaign = campaign;
        }
      }

      setLocationCampaign(newLocationCampaign);

      const breadcrumbItems = [
        { text: "Campaigns", href: UI_ROUTES.CAMPAIGN_MANAGEMENT },
      ];

      if (newLocationCampaign && newLocationCampaign.name)
        breadcrumbItems.push({
          text: newLocationCampaign.name,
          href: joinRoutes(
            UI_ROUTES.CAMPAIGN_MANAGEMENT,
            newLocationCampaign.name,
          ),
        });

      cmc.breadcrumbs.setBreadcrumbItems(breadcrumbItems);
    }

    setLocationCampaignAsync();
  }, [window.location.hash]);

  const { notifications, notify } = useNotifications();

  const onDeleteInit = () => setShowDeleteModal(true);
  const onEditInit = () => {
    navigate(`${UI_ROUTES.CAMPAIGN_EDIT}#${selectedItems[0].id}`);
  };
  const onDeleteDiscard = () => {
    setShowDeleteModal(false);
  };
  const onDeleteConfirm = async () => {
    const campaignsToDelete: CampaignItem[] = locationCampaign
      ? [locationCampaign]
      : selectedItems;
    setSelectedItems([]);
    setShowDeleteModal(false);

    const campaignsDeletePromises = campaignsToDelete.map(async (campaign) => {
      notify([
        {
          id: campaign.name,
          action: "delete",
          status: "in-progress",
          message: `Deleting campaign ${campaign.name}`,
        },
      ]);
      try {
        const cmd = new DeleteCampaignCommand({ name: campaign.name });
        const response = await api.client.send(cmd);
        if (response.$metadata.httpStatusCode == 200) {
          notify([
            {
              id: campaign.name,
              action: "delete",
              status: "success",
              message: `Successfully deleted campaign ${campaign.name}`,
            },
          ]);
        } else {
          notify([
            {
              id: campaign.name,
              action: "delete",
              status: "error",
              message: `Error deleting campaign ${campaign.name}`,
            },
          ]);
        }
      } catch (err) {
        notify([
          {
            id: campaign.name,
            action: "delete",
            status: "error",
            message: `Error deleting campaign ${campaign.name}`,
          },
        ]);
        console.log(err);
      }
    });
    await Promise.all(campaignsDeletePromises);
    fetchCampaigns();
  };

  useEffect(() => {
    setIsLoading(true);
    setError(null);

    if (window.location.hash.length > 0) {
      setIsLoading(false);
      return;
    }

    async function getCampaignsSummary() {
      try {
        await fetchCampaigns();
        setShowDeleteModal(false);
      } catch (err) {
        setError(err);
      } finally {
        setIsLoading(false);
      }
    }
    getCampaignsSummary();
  }, [window.location.hash]);

  return (
    <>
      {window.location.hash && !locationCampaign ? (
        <StatusIndicator type="loading">Loading...</StatusIndicator>
      ) : locationCampaign ? (
        <CampaignDetailsPage
          campaignName={locationCampaign.name}
          onDeleteInit={onDeleteInit}
          notifications={notifications}
        />
      ) : (
        <CampaignsPage
          campaigns={campaigns}
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
        campaigns={locationCampaign ? [locationCampaign] : selectedItems}
      />
    </>
  );
}
