// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

export const API_NAME = "api";
export const APP_TRADEMARK_NAME = "Connected Mobility Solution on AWS";

export const DELAY_AFTER_DELETE_MS = 2000; // 2 seconds

export const UI_ROUTES = {
  ROOT: "/",
  FLEET_MANAGEMENT: "/fleets/management",
  FLEET_VEHICLES_MAP: "/fleets/vehicles-map",
  FLEET_CREATE: "/fleets/create",
  FLEET_EDIT: "/fleets/edit",
  FLEET_ASSOCIATE_VEHICLES: "/fleets/associate-vehicles",
  VEHICLE_MANAGEMENT: "/vehicles/management",
  VEHICLE_DASHBOARD: "/vehicles/dashboard",
  VEHICLE_CREATE: "/vehicles/create",
  VEHICLE_EDIT: "/vehicles/edit",
  CAMPAIGN_MANAGEMENT: "/campaigns/management",
  CAMPAIGN_CREATE: "/campaigns/create",
  CAMPAIGN_EDIT: "/campaigns/edit",
  ALERTS_MAINTENANCE: "/alerts/maintenance",
};

export const ERROR_MESSAGES = {
  UNAUTHORIZED: "Request failed with status code 403",
};

export const LANDING_PAGE_URL =
  "https://aws.amazon.com/solutions/implementations/connected-mobility-solution-on-aws/";

export const FEEDBACK_ISSUES_URL =
  "https://github.com/aws-solutions/connected-mobility-solution-on-aws/issues/new/choose";

export const IG_ROOT =
  "https://docs.aws.amazon.com/solutions/latest/connected-mobility-solution-on-aws";
export const IG_URLS = {
  SUPPORT: `${IG_ROOT}/contact-aws-support.html`,
};
