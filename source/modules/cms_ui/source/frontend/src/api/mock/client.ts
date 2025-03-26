// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {
  FleetManagementClient,
  FleetManagementClientConfig,
  ListVehiclesInFleetCommand,
  GetFleetCommand,
  ListFleetsCommand,
  ListCampaignsForTargetCommand,
  FleetItem,
  ListVehiclesCommand,
  GetVehicleCommand,
  ListFleetsForVehicleCommand,
  ListSignalCatalogsCommand,
  CreateFleetCommand,
  DeleteFleetCommand,
  DeleteVehicleCommand,
  DeleteCampaignCommand,
  DisassociateVehicleCommand,
  EditFleetCommand,
  CampaignItem,
  VehicleItem,
  StartCampaignCommand,
  StopCampaignCommand,
  CampaignStatus,
  ListDecoderManifestsCommand,
  EditVehicleCommand,
  CreateVehicleCommand,
  SignalCatalogItem,
  DecoderManifestItem,
  AssociateVehiclesToFleetCommand,
  ListCampaignsCommand,
  GetCampaignCommand,
} from "@com.cms.fleetmanagement/api-client";
import { Command } from "@smithy/smithy-client";
import {
  ALL_FLEETS,
  FLEET_CAMPAIGNS,
  FLEET_VEHICLES,
  VEHICLES,
  SIGNAL_CATALOGS,
  DECODER_MANIFESTS,
  FleetSummary,
  getVehiclesForFleet,
  getFleets,
} from "@/api/mock/data/fleets-data";

export class MockFleetManagementClient extends FleetManagementClient {
  private ALL_FLEETS: FleetSummary[];
  private FLEET_CAMPAIGNS: CampaignItem[];
  private VEHICLES: VehicleItem[];
  private FLEET_VEHICLES: Record<string, string[]>;
  private SIGNAL_CATALOGS: SignalCatalogItem[];
  private DECODER_MANIFESTS: DecoderManifestItem[];

  constructor(config: FleetManagementClientConfig) {
    super(config);
    this.FLEET_CAMPAIGNS = FLEET_CAMPAIGNS;
    this.VEHICLES = VEHICLES;
    this.FLEET_VEHICLES = FLEET_VEHICLES;
    this.ALL_FLEETS = ALL_FLEETS;
    this.SIGNAL_CATALOGS = SIGNAL_CATALOGS;
    this.DECODER_MANIFESTS = DECODER_MANIFESTS;
  }

  async send<T extends Command<any, any, any>>(command: T): Promise<any> {
    if (command instanceof ListFleetsCommand) {
      return Promise.resolve({
        fleets: getFleets(
          this.ALL_FLEETS,
          this.VEHICLES,
          this.FLEET_VEHICLES,
          this.FLEET_CAMPAIGNS,
        ) as FleetItem[],
      });
    } else if (command instanceof GetFleetCommand) {
      return Promise.resolve(
        getFleets(
          this.ALL_FLEETS,
          this.VEHICLES,
          this.FLEET_VEHICLES,
          this.FLEET_CAMPAIGNS,
        ).find((fleet) => fleet.id === command.input.id),
      );
    } else if (command instanceof ListCampaignsForTargetCommand) {
      return Promise.resolve({
        campaigns: this.FLEET_CAMPAIGNS.filter(
          (campaign) => campaign.targetId === command.input.targetId,
        ),
      });
    } else if (command instanceof ListVehiclesInFleetCommand) {
      return Promise.resolve({
        vehicles: getVehiclesForFleet(
          command.input.id,
          this.VEHICLES,
          this.FLEET_VEHICLES,
        ),
      });
    } else if (command instanceof ListVehiclesCommand) {
      return Promise.resolve({
        vehicles: this.VEHICLES,
      });
    } else if (command instanceof GetVehicleCommand) {
      return Promise.resolve(
        this.VEHICLES.find((vehicle) => vehicle.name === command.input.name),
      );
    } else if (command instanceof ListFleetsForVehicleCommand) {
      const associatedFleets: FleetItem[] = [];

      for (const [fleetId, vehicleNames] of Object.entries(
        this.FLEET_VEHICLES,
      )) {
        if (vehicleNames.includes(command.input.name)) {
          const fleet = getFleets(
            this.ALL_FLEETS,
            this.VEHICLES,
            this.FLEET_VEHICLES,
            this.FLEET_CAMPAIGNS,
          ).find((f) => f.id === fleetId);
          if (fleet) {
            associatedFleets.push(fleet);
          } else {
            console.warn(`Fleet with ID ${fleetId} not found.`);
          }
        }
      }
      return Promise.resolve({ fleets: associatedFleets });
    } else if (command instanceof ListSignalCatalogsCommand) {
      return Promise.resolve({ signalCatalogs: this.SIGNAL_CATALOGS });
    } else if (command instanceof CreateFleetCommand) {
      this.ALL_FLEETS.push({
        id: command.input.entry.id,
        name: command.input.entry.name,
      });
      this.FLEET_VEHICLES[command.input.entry.id] = [];
      return Promise.resolve({ $metadata: { httpStatusCode: 200 } });
    } else if (command instanceof DeleteFleetCommand) {
      this.ALL_FLEETS.splice(
        this.ALL_FLEETS.findIndex((item) => item.id === command.input.id),
        1,
      );
      return Promise.resolve({ $metadata: { httpStatusCode: 200 } });
    } else if (command instanceof DeleteCampaignCommand) {
      this.FLEET_CAMPAIGNS.splice(
        this.FLEET_CAMPAIGNS.findIndex(
          (item) => item.name === command.input.name,
        ),
        1,
      );
      return Promise.resolve({});
    } else if (command instanceof DeleteVehicleCommand) {
      this.VEHICLES.splice(
        this.VEHICLES.findIndex((item) => item.name === command.input.name),
        1,
      );
      return Promise.resolve({ $metadata: { httpStatusCode: 200 } });
    } else if (command instanceof DisassociateVehicleCommand) {
      this.FLEET_VEHICLES[command.input.fleetId] = this.FLEET_VEHICLES[
        command.input.fleetId
      ].filter((name) => name !== command.input.name);
      return Promise.resolve({});
    } else if (command instanceof EditFleetCommand) {
      this.ALL_FLEETS.forEach((item) => {
        if (item.id === command.input.id) {
          item.name = command.input.entry.name;
        }
      });
      return Promise.resolve({ $metadata: { httpStatusCode: 200 } });
    } else if (command instanceof CreateVehicleCommand) {
      this.VEHICLES.push({
        name: command.input.entry.name,
        status: "ACTIVE",
        attributes: {
          make: command.input.entry.make,
          model: command.input.entry.model,
          year: command.input.entry.year,
          licensePlate: command.input.entry.licensePlate,
        },
      });
      return Promise.resolve({ $metadata: { httpStatusCode: 200 } });
    } else if (command instanceof ListDecoderManifestsCommand) {
      return Promise.resolve({ decoderManifests: this.DECODER_MANIFESTS });
    } else if (command instanceof EditVehicleCommand) {
      this.VEHICLES.forEach((vehicle) => {
        if (vehicle.name === command.input.name && vehicle.attributes) {
          vehicle.attributes.make = command.input.entry.make;
          vehicle.attributes.model = command.input.entry.model;
          vehicle.attributes.year = command.input.entry.year;
          vehicle.attributes.licensePlate = command.input.entry.licensePlate;
        }
      });
      return Promise.resolve({ $metadata: { httpStatusCode: 200 } });
    } else if (command instanceof StartCampaignCommand) {
      const campaign = this.FLEET_CAMPAIGNS.find(
        (c) => c.name === command.input.name,
      );
      if (campaign) {
        campaign.status = CampaignStatus.RUNNING;
      }
      return Promise.resolve({});
    } else if (command instanceof StopCampaignCommand) {
      const campaign = this.FLEET_CAMPAIGNS.find(
        (c) => c.name === command.input.name,
      );
      if (campaign) {
        campaign.status = CampaignStatus.SUSPENDED;
      }
      return Promise.resolve({});
    } else if (command instanceof AssociateVehiclesToFleetCommand) {
      this.FLEET_VEHICLES[command.input.id].push(...command.input.vehicleNames);
      return Promise.resolve({ $metadata: { httpStatusCode: 200 } });
    } else if (command instanceof ListCampaignsCommand) {
      return Promise.resolve({
        campaigns: this.FLEET_CAMPAIGNS,
      });
    } else if (command instanceof GetCampaignCommand) {
      return Promise.resolve(
        this.FLEET_CAMPAIGNS.filter(
          (campaign) => campaign.name === command.input.name,
        )[0],
      );
    }
  }
}
