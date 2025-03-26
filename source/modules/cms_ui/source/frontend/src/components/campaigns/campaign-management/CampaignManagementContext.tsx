// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { CampaignItem } from "@com.cms.fleetmanagement/api-client";
import { BreadcrumbGroupProps } from "@cloudscape-design/components";
import { createContext, useMemo, useState } from "react";

type BreadcrumbContextType = {
  breadcrumbItems: BreadcrumbGroupProps["items"];
  setBreadcrumbItems: (items: BreadcrumbGroupProps["items"]) => void;
};

type CampaignContextType = {
  locationCampaign: CampaignItem | undefined;
  setLocationCampaign: (campaign: CampaignItem | undefined) => void;
};

type CampaignManagementContextType = {
  breadcrumbs: BreadcrumbContextType;
  campaign: CampaignContextType;
};

const DEFAULT_CONTEXT: CampaignManagementContextType = {
  breadcrumbs: {
    breadcrumbItems: [],
    setBreadcrumbItems: () => {},
  },
  campaign: {
    locationCampaign: undefined,
    setLocationCampaign: () => {},
  },
};

export const CampaignManagementContext =
  createContext<CampaignManagementContextType>(DEFAULT_CONTEXT);

export const CampaignManagementContextProvider = ({
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

  const [locationCampaign, setLocationCampaign] = useState<
    CampaignItem | undefined
  >(undefined);

  const campaign = {
    locationCampaign: locationCampaign,
    setLocationCampaign: setLocationCampaign,
  };

  const contextValue = useMemo(
    () => ({
      breadcrumbs: breadcrumbs,
      campaign: campaign,
    }),
    [breadcrumbs, campaign],
  );

  return (
    <CampaignManagementContext.Provider value={contextValue}>
      {children}
    </CampaignManagementContext.Provider>
  );
};
