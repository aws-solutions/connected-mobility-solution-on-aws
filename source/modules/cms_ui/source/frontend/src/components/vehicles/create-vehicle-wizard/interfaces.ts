// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { ReactNode } from "react";

import {
  CreateVehicleEntry,
  AssociateVehiclesToFleetInput,
} from "@com.cms.fleetmanagement/api-client";

export interface CreateVehicleFormData {
  createVehicle: CreateVehicleEntry;
  associateFleet: AssociateVehiclesToFleetInput;
}

export interface ToolsContent {
  title: string;
  links: {
    href: string;
    text: string;
  }[];
  content: ReactNode;
}
