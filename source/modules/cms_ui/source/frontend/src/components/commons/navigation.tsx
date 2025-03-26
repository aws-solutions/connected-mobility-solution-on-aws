// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { UI_ROUTES } from "@/utils/constants";
import SideNavigation, {
  SideNavigationProps,
} from "@cloudscape-design/components/side-navigation";
import { useNavigate } from "react-router-dom";

const navHeader = { text: "Fleet Management", href: UI_ROUTES.ROOT };
export const navItems: SideNavigationProps["items"] = [
  { type: "link", text: "Dashboard", href: UI_ROUTES.ROOT },
  {
    type: "section",
    text: "Fleets",
    items: [
      {
        type: "link",
        text: "Manage Fleets",
        href: UI_ROUTES.FLEET_MANAGEMENT,
      },
      {
        type: "link",
        text: "Map View",
        href: UI_ROUTES.FLEET_VEHICLES_MAP,
      },
    ],
  },
  {
    type: "section",
    text: "Vehicles",
    items: [
      {
        type: "link",
        text: "Manage Vehicles",
        href: UI_ROUTES.VEHICLE_MANAGEMENT,
      },
    ],
  },
  {
    type: "section",
    text: "Campaigns",
    items: [
      {
        type: "link",
        text: "Manage Campaigns",
        href: UI_ROUTES.CAMPAIGN_MANAGEMENT,
      },
    ],
  },
  {
    type: "section",
    text: "Alerts",
    items: [
      {
        type: "link",
        text: "Maintenance Alerts",
        href: UI_ROUTES.ALERTS_MAINTENANCE,
      },
      // {
      //   type: "link",
      //   text: "Service Predictions",
      //   href: UI_ROUTES.ALERTS_SVC_PREDICTIONS,
      // },
    ],
  },
];

interface NavigationProps {
  activeHref?: string;
  header?: SideNavigationProps["header"];
  items?: SideNavigationProps["items"];
  onFollowHandler?: SideNavigationProps["onFollow"];
}

export function Navigation({
  activeHref,
  header = navHeader,
  items = navItems,
  onFollowHandler = undefined,
}: NavigationProps) {
  const navigate = useNavigate();
  const onFollowNavigationHandler: SideNavigationProps["onFollow"] = (
    event,
  ) => {
    event.preventDefault();
    navigate(event.detail.href);
  };

  return (
    <SideNavigation
      items={items}
      header={header}
      activeHref={activeHref}
      onFollow={onFollowHandler ?? onFollowNavigationHandler}
    />
  );
}
