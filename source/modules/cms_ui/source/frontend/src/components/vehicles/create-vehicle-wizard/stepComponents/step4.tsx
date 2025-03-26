// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React from "react";

import Box from "@cloudscape-design/components/box";
import Button from "@cloudscape-design/components/button";
import Container from "@cloudscape-design/components/container";
import ExpandableSection from "@cloudscape-design/components/expandable-section";
import Header from "@cloudscape-design/components/header";
import KeyValuePairs from "@cloudscape-design/components/key-value-pairs";
import SpaceBetween from "@cloudscape-design/components/space-between";
import { CreateVehicleFormData } from "../interfaces";
import { TagsPanel } from "../../../commons";

export interface CreateVehicleInputPanelProps {
  loadHelpPanelContent: any;
  inputData: CreateVehicleFormData;
  setTagsInputData: any;
}

export function CreateVehicleReviewPanel({
  loadHelpPanelContent,
  inputData,
  setTagsInputData: setInputTagsData,
}: CreateVehicleInputPanelProps) {
  return (
    <Box margin={{ bottom: "l" }}>
      <SpaceBetween size="xxl">
        <SpaceBetween size="xs" className="step-1-review">
          <Container
            header={
              <Header variant="h2" headingTagOverride="h3">
                Decoder Manifest
              </Header>
            }
          >
            <KeyValuePairs
              columns={2}
              items={[
                {
                  label: "Vehicle Name",
                  value: inputData.createVehicle.name,
                },
                {
                  label: "Decoder Manifest",
                  value: inputData.createVehicle.decoderManifestName,
                },
              ]}
            />
          </Container>
        </SpaceBetween>
        <SpaceBetween size="xs" className="step-2-review">
          <Container
            header={
              <Header variant="h2" headingTagOverride="h3">
                Vehicle Attributes
              </Header>
            }
          >
            <KeyValuePairs
              columns={2}
              items={[
                { label: "VIN", value: inputData.createVehicle.vin },
                { label: "Make", value: inputData.createVehicle.make },
                { label: "Model", value: inputData.createVehicle.model },
                { label: "Year", value: inputData.createVehicle.year },
                {
                  label: "License Plate",
                  value: inputData.createVehicle.licensePlate,
                },
              ]}
            />
          </Container>
        </SpaceBetween>
        <SpaceBetween size="xs" className="step-3-review">
          <Container
            header={
              <Header variant="h2" headingTagOverride="h3">
                Associate Fleet
              </Header>
            }
          >
            <KeyValuePairs
              columns={2}
              items={[{ label: "Fleet", value: inputData.associateFleet.id }]}
            />
          </Container>
        </SpaceBetween>
        <TagsPanel
          loadHelpPanelContent={loadHelpPanelContent}
          inputData={inputData.createVehicle}
          setInputData={setInputTagsData}
        />
      </SpaceBetween>
    </Box>
  );
}
