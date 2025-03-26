// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { Context } from "aws-lambda";
import {
  ListFleetsOutput,
  FleetItem,
  FleetManagementService,
  GetFleetInput,
  ListCampaignsForTargetInput,
  ListCampaignsForTargetOutput,
  ListVehiclesInFleetInput,
  ListVehiclesInFleetOutput,
  ListVehiclesOutput,
  GetVehicleInput,
  VehicleItem,
  ListFleetsForVehicleInput,
  ListFleetsForVehicleOutput,
  ListSignalCatalogsOutput,
  CreateFleetInput,
  DeleteFleetInput,
  DeleteCampaignInput,
  DeleteVehicleInput,
  DisassociateVehicleInput,
  EditFleetInput,
  CreateVehicleInput,
  ListDecoderManifestsOutput,
  EditVehicleInput,
  StartCampaignInput,
  StopCampaignInput,
  AssociateVehiclesToFleetInput,
  GetCampaignInput,
  CampaignItem,
} from "@com.cms.fleetmanagement/api-server";
import { listVehicles } from "./apis/list-vehicles";
import { getVehicle } from "./apis/get-vehicle";
import { listFleets } from "./apis/list-fleets";
import { getFleet } from "./apis/get-fleet";
import { listCampaignsForTarget } from "./apis/list-campaigns-for-target";
import { listVehiclesInFleet } from "./apis/list-vehicles-in-fleet";
import { listFleetsForVehicle } from "./apis/list-fleets-for-vehicles";
import { listSignalCatalogs } from "./apis/list-signal-catalogs";
import { createFleet } from "./apis/create-fleet";
import { deleteFleet } from "./apis/delete-fleet";
import { deleteCampaign } from "./apis/delete-campaign";
import { deleteVehicle } from "./apis/delete-vehicle";
import { disassociateVehicle } from "./apis/disassociate-vehicle";
import { editFleet } from "./apis/edit-fleet";
import { createVehicle } from "./apis/create-vehicle";
import { editVehicle } from "./apis/edit-vehicle";
import { listDecoderManifests } from "./apis/list-decoder-manifests";
import { startCampaign } from "./apis/start-campaign";
import { stopCampaign } from "./apis/stop-campaign";
import { associateVehiclesToFleet } from "./apis/associate-vehicles-to-fleet";
import { listCampaigns } from "./apis/list-campaigns";
import { getCampaign } from "./apis/get-campaign";

export class FleetManagement implements FleetManagementService<Context> {
  async ListFleets(): Promise<ListFleetsOutput> {
    return await listFleets();
  }

  async GetFleet(input: GetFleetInput): Promise<FleetItem> {
    return await getFleet(input);
  }

  async ListCampaignsForTarget(
    input: ListCampaignsForTargetInput,
  ): Promise<ListCampaignsForTargetOutput> {
    return await listCampaignsForTarget(input);
  }

  async ListVehiclesInFleet(
    input: ListVehiclesInFleetInput,
  ): Promise<ListVehiclesInFleetOutput> {
    return await listVehiclesInFleet(input);
  }

  async ListVehicles(): Promise<ListVehiclesOutput> {
    return await listVehicles();
  }

  async GetVehicle(input: GetVehicleInput): Promise<VehicleItem> {
    return await getVehicle(input);
  }

  async ListFleetsForVehicle(
    input: ListFleetsForVehicleInput,
  ): Promise<ListFleetsForVehicleOutput> {
    return await listFleetsForVehicle(input);
  }

  async ListSignalCatalogs(): Promise<ListSignalCatalogsOutput> {
    return await listSignalCatalogs();
  }

  async CreateFleet(input: CreateFleetInput): Promise<{}> {
    return await createFleet(input);
  }

  async DeleteFleet(input: DeleteFleetInput): Promise<{}> {
    return await deleteFleet(input);
  }

  async DeleteCampaign(input: DeleteCampaignInput): Promise<{}> {
    return await deleteCampaign(input);
  }

  async DeleteVehicle(input: DeleteVehicleInput): Promise<{}> {
    return await deleteVehicle(input);
  }

  async DisassociateVehicle(input: DisassociateVehicleInput): Promise<{}> {
    return await disassociateVehicle(input);
  }

  async EditFleet(input: EditFleetInput): Promise<{}> {
    return await editFleet(input);
  }

  async CreateVehicle(input: CreateVehicleInput): Promise<{}> {
    return await createVehicle(input);
  }

  async ListDecoderManifests(): Promise<ListDecoderManifestsOutput> {
    return await listDecoderManifests();
  }

  async EditVehicle(input: EditVehicleInput): Promise<{}> {
    return await editVehicle(input);
  }

  async StartCampaign(input: StartCampaignInput): Promise<{}> {
    return await startCampaign(input);
  }

  async StopCampaign(input: StopCampaignInput): Promise<{}> {
    return await stopCampaign(input);
  }

  async AssociateVehiclesToFleet(
    input: AssociateVehiclesToFleetInput,
  ): Promise<{}> {
    return await associateVehiclesToFleet(input);
  }

  async ListCampaigns(): Promise<{}> {
    return await listCampaigns();
  }

  async GetCampaign(input: GetCampaignInput): Promise<CampaignItem> {
    return await getCampaign(input);
  }
}
