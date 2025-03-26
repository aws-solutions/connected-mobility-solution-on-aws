// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React, { useRef, useState, useContext } from "react";
import AppLayout, {
  AppLayoutProps,
} from "@cloudscape-design/components/app-layout";
import HelpPanel from "@cloudscape-design/components/help-panel";
import Wizard, { WizardProps } from "@cloudscape-design/components/wizard";
import { ExternalLinkGroup, InfoLink } from "../../commons";
import { Navigation } from "@/components/commons";
import { CreateVehicleFormData, ToolsContent } from "./interfaces";
import {
  CreateVehicleInputPanel,
  CreateVehicleInputPanelRef,
} from "./stepComponents/step1";
import {
  CreateVehicleAttributesInputPanel,
  CreateVehicleAttributesInputPanelRef,
} from "./stepComponents/step2";
import {
  AssociateVehicleFleetPanel,
  AssociateVehicleFleetPanelRef,
} from "./stepComponents/step3";
import { CreateVehicleReviewPanel } from "./stepComponents/step4";
import { TOOLS_CONTENT } from "./steps-config";
import { Breadcrumbs } from "@/components/commons/breadcrumbs";
import { UI_ROUTES } from "@/utils/constants";
import { ApiContext } from "@/api/provider";
import { useNavigate } from "react-router-dom";
import {
  CreateVehicleCommand,
  AssociateVehiclesToFleetCommand,
} from "@com.cms.fleetmanagement/api-client";
import {
  CreateVehicleProgress,
  CreateVehicleProgressStep,
  StatusType,
} from "./progress";

const steps = [
  {
    title: "Select decoder manifest",
    stateKey: "decoderManifest",
    StepContent: CreateVehicleInputPanel,
  },
  {
    title: "Specify vehicle attributes",
    stateKey: "attributes",
    StepContent: CreateVehicleAttributesInputPanel,
  },
  {
    title: "Associate fleet",
    stateKey: "fleet",
    StepContent: AssociateVehicleFleetPanel,
  },
  {
    title: "Review and create",
    stateKey: "review",
    StepContent: CreateVehicleReviewPanel,
  },
] as const;

const i18nStrings = {
  submitButton: "Create vehicle",
  stepNumberLabel: (stepNumber: number) => `Step ${stepNumber}`,
  collapsedStepsLabel: (stepNumber: number, stepsCount: number) =>
    `Step ${stepNumber} of ${stepsCount}`,
};

const getDefaultToolsContent = (activeIndex: number) =>
  TOOLS_CONTENT[steps[activeIndex].stateKey].default;

const getFormattedToolsContent = (tools: ToolsContent) => (
  <HelpPanel
    header={<h2>{tools.title}</h2>}
    footer={<ExternalLinkGroup items={tools.links} />}
  >
    {tools.content}
  </HelpPanel>
);

const useTools = () => {
  const [toolsContent, setToolsContent] = useState(
    getFormattedToolsContent(getDefaultToolsContent(0)),
  );
  const [isToolsOpen, setIsToolsOpen] = useState(false);
  const appLayoutRef = useRef<AppLayoutProps.Ref>(null);

  const setFormattedToolsContent = (tools: ToolsContent) => {
    setToolsContent(getFormattedToolsContent(tools));
  };

  const setHelpPanelContent = (tools: ToolsContent) => {
    if (tools) {
      setFormattedToolsContent(tools);
    }
    setIsToolsOpen(true);
    appLayoutRef.current?.focusToolsClose();
  };
  const closeTools = () => setIsToolsOpen(false);
  const onToolsChange: AppLayoutProps["onToolsChange"] = (evt) =>
    setIsToolsOpen(evt.detail.open);

  return {
    toolsContent,
    isToolsOpen,
    setHelpPanelContent,
    closeTools,
    setFormattedToolsContent,
    onToolsChange,
    appLayoutRef,
  };
};

const useWizard = (
  closeTools: () => void,
  setFormattedToolsContent: (tools: ToolsContent) => void,
  step1Ref: CreateVehicleInputPanelRef,
  step2Ref: CreateVehicleAttributesInputPanelRef,
  step3Ref: AssociateVehicleFleetPanelRef,
) => {
  const [activeStepIndex, setActiveStepIndex] = useState(0);

  const setActiveStepIndexAndCloseTools = (index: number) => {
    setActiveStepIndex(index);
    setFormattedToolsContent(getDefaultToolsContent(index));
    closeTools();
  };

  const onNavigate: WizardProps["onNavigate"] = (evt) => {
    if (evt.detail.requestedStepIndex > activeStepIndex) {
      //only care if moving to next page, need to allow the user to go back without being impacted by errors.
      let valid = true;
      if (activeStepIndex === 0 && step1Ref.current) {
        valid = step1Ref.current.validate();
      } else if (activeStepIndex === 1 && step2Ref.current) {
        valid = step2Ref.current.validate();
      } else if (activeStepIndex === 2 && step3Ref.current) {
        valid = step3Ref.current.validate();
      }
      if (!valid) {
        return;
      }
    }
    setActiveStepIndexAndCloseTools(evt.detail.requestedStepIndex);
  };

  return {
    activeStepIndex,
    onNavigate,
  };
};

const defaultData: CreateVehicleFormData = {
  createVehicle: {
    name: "",
    decoderManifestName: "",
    vin: "",
    make: "",
    model: "",
    year: 0,
    licensePlate: "",
    tags: [],
  },
  associateFleet: {
    id: "",
    vehicleNames: [],
  },
};

enum CreateVehicleStep {
  CREATE_VEHICLE = "Create Vehicle",
  ASSOCIATE_FLEET = "Associate Fleet",
}

export const CREATE_VEHICLE_PROGRESS_STEPS: Record<
  string,
  CreateVehicleProgressStep
> = {
  [CreateVehicleStep.CREATE_VEHICLE]: {
    label: CreateVehicleStep.CREATE_VEHICLE,
    status: "pending",
  },
  [CreateVehicleStep.ASSOCIATE_FLEET]: {
    label: CreateVehicleStep.ASSOCIATE_FLEET,
    status: "pending",
  },
};

export const CreateVehicleWizard = () => {
  const {
    toolsContent,
    isToolsOpen,
    setHelpPanelContent,
    closeTools,
    setFormattedToolsContent,
    onToolsChange,
    appLayoutRef,
  } = useTools();
  const step1Ref = useRef<CreateVehicleInputPanelRef>(null);
  const step2Ref = useRef<CreateVehicleAttributesInputPanelRef>(null);
  const step3Ref = useRef<AssociateVehicleFleetPanelRef>(null);

  const { activeStepIndex, onNavigate } = useWizard(
    closeTools,
    setFormattedToolsContent,
    step1Ref,
    step2Ref,
    step3Ref,
  );

  const api = useContext(ApiContext);
  const navigate = useNavigate();

  const [wizardSubmitted, setWizardSubmitted] = useState<boolean>(false);
  const [createVehicleProgressSteps, setCreateVehicleProgressSteps] = useState<
    Record<CreateVehicleStep, CreateVehicleProgressStep>
  >(CREATE_VEHICLE_PROGRESS_STEPS);
  const updateStepStatus = (step: CreateVehicleStep, newStatus: StatusType) => {
    setCreateVehicleProgressSteps((prev) => ({
      ...prev,
      [step]: {
        ...prev[step],
        status: newStatus,
      },
    }));
  };

  const onCancel = () => {
    navigate(UI_ROUTES.VEHICLE_MANAGEMENT);
    setData(defaultData);
  };

  const onSubmit = async () => {
    try {
      updateStepStatus(CreateVehicleStep.CREATE_VEHICLE, "in-progress");
      const createVehicleCommand = new CreateVehicleCommand({
        entry: data.createVehicle,
      });
      const createVehicleResponse = await api.client.send(createVehicleCommand);

      if (createVehicleResponse.$metadata.httpStatusCode === 200) {
        updateStepStatus(CreateVehicleStep.CREATE_VEHICLE, "success");
      } else {
        updateStepStatus(CreateVehicleStep.CREATE_VEHICLE, "error");
      }

      updateStepStatus(CreateVehicleStep.ASSOCIATE_FLEET, "in-progress");
      const associateFleetCommand = new AssociateVehiclesToFleetCommand(
        data.associateFleet,
      );
      const associateFleetResponse = await api.client.send(
        associateFleetCommand,
      );
      if (associateFleetResponse.$metadata.httpStatusCode === 200) {
        updateStepStatus(CreateVehicleStep.ASSOCIATE_FLEET, "success");
      } else {
        updateStepStatus(CreateVehicleStep.ASSOCIATE_FLEET, "error");
      }
      navigate(UI_ROUTES.VEHICLE_MANAGEMENT, {
        state: {
          notification: {
            id: data.createVehicle.name,
            status:
              createVehicleResponse.$metadata.httpStatusCode === 200 &&
              associateFleetResponse.$metadata.httpStatusCode === 200
                ? "success"
                : "error",
          },
        },
      });
    } catch (error) {
      navigate(UI_ROUTES.VEHICLE_MANAGEMENT, {
        state: {
          notification: {
            id: data.createVehicle.name,
            status: "error",
          },
        },
      });
    }
  };

  const [data, _setData] = useState<CreateVehicleFormData>(defaultData);
  const setData = (updateObj = {}) =>
    _setData((prevData) => ({ ...prevData, ...updateObj }));

  const setTagsData = (updateObj = {}) =>
    _setData((prevData) => ({
      ...prevData,
      createVehicle: {
        ...prevData.createVehicle,
        ...updateObj,
      },
    }));

  const wizardSteps = [
    {
      title: "Select decoder manifest",
      info: (
        <InfoLink
          onFollow={() =>
            setHelpPanelContent(TOOLS_CONTENT.decoderManifest.default)
          }
        />
      ),
      content: (
        <CreateVehicleInputPanel
          ref={step1Ref}
          loadHelpPanelContent={setHelpPanelContent}
          inputData={data}
          setInputData={setData}
        />
      ),
    },
    {
      title: "Specify vehicle attributes",
      info: (
        <InfoLink
          onFollow={() => setHelpPanelContent(TOOLS_CONTENT.attributes.default)}
        />
      ),
      content: (
        <CreateVehicleAttributesInputPanel
          ref={step2Ref}
          loadHelpPanelContent={setHelpPanelContent}
          inputData={data}
          setInputData={setData}
        />
      ),
    },
    {
      title: "Associate fleet",
      info: (
        <InfoLink
          onFollow={() => setHelpPanelContent(TOOLS_CONTENT.fleet.default)}
        />
      ),
      content: (
        <AssociateVehicleFleetPanel
          ref={step3Ref}
          loadHelpPanelContent={setHelpPanelContent}
          inputData={data}
          setInputData={setData}
        />
      ),
    },
    {
      title: "Review and create",
      info: (
        <InfoLink
          onFollow={() => setHelpPanelContent(TOOLS_CONTENT.review.default)}
        />
      ),
      content: (
        <CreateVehicleReviewPanel
          loadHelpPanelContent={setHelpPanelContent}
          inputData={data}
          setTagsInputData={setTagsData}
        />
      ),
    },
  ];

  return (
    <AppLayout
      ref={appLayoutRef}
      navigation={<Navigation />}
      tools={toolsContent}
      toolsOpen={isToolsOpen}
      onToolsChange={onToolsChange}
      breadcrumbs={
        <Breadcrumbs
          items={[
            { text: "Vehicles", href: UI_ROUTES.VEHICLE_MANAGEMENT },
            { text: "Create Vehicle", href: UI_ROUTES.VEHICLE_CREATE },
          ]}
        />
      }
      contentType="wizard"
      content={
        <div>
          {wizardSubmitted ? (
            <CreateVehicleProgress steps={createVehicleProgressSteps} />
          ) : (
            <Wizard
              steps={wizardSteps}
              activeStepIndex={activeStepIndex}
              i18nStrings={i18nStrings}
              onNavigate={onNavigate}
              onCancel={onCancel}
              onSubmit={onSubmit}
            />
          )}
        </div>
      }
    />
  );
};
