// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React, { useState, useContext, ReactElement, useEffect } from "react";
import { ApiContext } from "@/api/provider";
import {
  Button,
  Form,
  Header,
  SpaceBetween,
} from "@cloudscape-design/components";
import { InfoLink } from "../../../commons";
import { EditVehicleInputPanel } from "./input-panel";
import { CreateVehicleAttributesInputPanel } from "./attributes-panel";
import { TagsPanel } from "../../../commons";
import {
  EditVehicleEntry,
  EditVehicleCommand,
  GetVehicleCommand,
} from "@com.cms.fleetmanagement/api-client";
import { UI_ROUTES } from "@/utils/constants";
import { Modal, Box } from "@cloudscape-design/components";
import { useNavigate } from "react-router-dom";
import useLocationHash from "../../vehicle-management/use-location-hash";

interface BaseFormProps {
  content: React.ReactElement;
  onCancelClick: any;
  onSubmitClick: any;
  header: ReactElement;
}

export function FormHeader({ loadHelpPanelContent }: any) {
  return (
    <Header
      variant="h1"
      info={
        <InfoLink
          id="form-main-info-link"
          onFollow={() => loadHelpPanelContent(0)}
        />
      }
      description={"Edit a vehicle entity that currently exists."}
    >
      Edit vehicle
    </Header>
  );
}

function FormActions({ onCancelClick, onSubmitClick }: any) {
  return (
    <SpaceBetween direction="horizontal" size="xs">
      <Button variant="link" onClick={onCancelClick}>
        Cancel
      </Button>
      <Button data-testid="create" variant="primary" onClick={onSubmitClick}>
        Edit vehicle
      </Button>
    </SpaceBetween>
  );
}

function BaseForm({
  content,
  onCancelClick,
  onSubmitClick,
  header,
}: BaseFormProps) {
  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        if (onSubmitClick) {
          onSubmitClick();
        }
      }}
    >
      <Form
        header={header}
        actions={
          <FormActions
            onCancelClick={onCancelClick}
            onSubmitClick={onSubmitClick}
          />
        }
        errorIconAriaLabel="Error"
      >
        {content}
      </Form>
    </form>
  );
}

const defaultData: EditVehicleEntry = {
  name: "",
  vin: "",
  make: "",
  model: "",
  year: 0,
  licensePlate: "",
  tags: [],
};

export function FormFull({ loadHelpPanelContent, header }: any) {
  const [data, _setData] = useState<EditVehicleEntry>(defaultData);
  const setData = (updateObj = {}) =>
    _setData((prevData) => ({ ...prevData, ...updateObj }));

  const api = useContext(ApiContext);

  const navigate = useNavigate();
  const locationHash = useLocationHash();

  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [modalConfig, setModalConfig] = useState<{
    title: string;
    message: string;
    type: "success" | "error";
  }>({
    title: "",
    message: "",
    type: "success",
  });

  const showModal = (
    type: "success" | "error",
    title: string,
    message: string,
  ) => {
    setModalConfig({
      type,
      title,
      message,
    });
    setModalVisible(true);
  };

  const handleModalDismiss = () => {
    setModalVisible(false);

    // If it was a successful submission, we might want to perform additional actions
    if (modalConfig.type === "success") {
      navigate(UI_ROUTES.VEHICLE_MANAGEMENT);
    }
  };

  useEffect(() => {
    async function setVehicle() {
      setLoading(true);
      const cmd = new GetVehicleCommand({ name: locationHash });
      const response = await api.client.send(cmd);
      setData({
        name: response.name,
        vin: response.attributes?.vin,
        make: response.attributes?.make,
        model: response.attributes?.model,
        year: response.attributes?.year,
        licensePlate: response.attributes?.licensePlate,
        tags: response?.tags || [],
      });
      setLoading(false);
    }

    setVehicle();
  }, [locationHash]);

  const editVehicle = async () => {
    try {
      const cmd = new EditVehicleCommand({ name: locationHash, entry: data });
      const response = await api.client.send(cmd);

      if (response.$metadata.httpStatusCode == 200) {
        showModal("success", "Success!", "Vehicle edited successfully.");
        // Reset form
        setData(defaultData);
      } else {
        showModal(
          "error",
          "Failed",
          "There was an error editing the vehicle. Please try again.",
        );
      }
    } catch (error) {
      showModal(
        "error",
        "Error",
        "An unexpected error occurred. Please try again later.",
      );
      console.error("Submit error:", error);
    } finally {
      setLoading(false);
    }
  };

  const onSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setLoading(true);
    await editVehicle();
  };

  if (loading) {
    return (
      <div>
        <Box textAlign="center" color="inherit">
          <p>Loading ...</p>
        </Box>
      </div>
    );
  }

  return (
    <div>
      <BaseForm
        header={header}
        content={
          <SpaceBetween size="l">
            <EditVehicleInputPanel
              loadHelpPanelContent={loadHelpPanelContent}
              inputData={data}
              setInputData={setData}
            />
            <CreateVehicleAttributesInputPanel
              loadHelpPanelContent={loadHelpPanelContent}
              inputData={data}
              setInputData={setData}
            />
            <TagsPanel
              loadHelpPanelContent={loadHelpPanelContent}
              inputData={data}
              setInputData={setData}
            />
          </SpaceBetween>
        }
        onCancelClick={() => {
          setData(defaultData);
          navigate(UI_ROUTES.VEHICLE_MANAGEMENT);
        }}
        onSubmitClick={onSubmit}
      />
      <Modal
        visible={modalVisible}
        onDismiss={handleModalDismiss}
        header={modalConfig.title}
        closeAriaLabel="Close modal"
      >
        <Box
          color={
            modalConfig.type === "success"
              ? "text-status-success"
              : "text-status-error"
          }
        >
          <SpaceBetween size="m">
            <Box>{modalConfig.message}</Box>
            <Button onClick={handleModalDismiss} variant="primary">
              {modalConfig.type === "success" ? "Continue" : "Close"}
            </Button>
          </SpaceBetween>
        </Box>
      </Modal>
    </div>
  );
}
