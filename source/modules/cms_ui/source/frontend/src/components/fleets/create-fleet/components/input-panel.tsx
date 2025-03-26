// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React, {
  useState,
  useCallback,
  useContext,
  useImperativeHandle,
  forwardRef,
  useRef,
} from "react";
import {
  Container,
  Input,
  FormField,
  SpaceBetween,
  Select,
  SelectProps,
  Textarea,
} from "@cloudscape-design/components";
import { InfoLink } from "../../../commons";
import { ApiContext } from "@/api/provider";
import {
  ListSignalCatalogsCommand,
  CreateFleetEntry,
} from "@com.cms.fleetmanagement/api-client";

type StatusType = "pending" | "loading" | "finished" | "error";

export interface CreateFleetInputPanelProps {
  loadHelpPanelContent: any;
  inputData: CreateFleetEntry;
  setInputData: any;
}

export interface CreateFleetInputPanelRef {
  validate: () => boolean;
}

export const CreateFleetInputPanel = forwardRef<
  CreateFleetInputPanelRef,
  CreateFleetInputPanelProps
>(function CreateFleetInputPanel(
  { loadHelpPanelContent, inputData, setInputData },
  ref,
) {
  const [options, setOptions] = useState<SelectProps.Option[]>([]);
  const [selectedOption, setSelectedOption] = useState<SelectProps.Option>();
  const [status, setStatus] = useState<StatusType>("pending");

  const [errors, setErrors] = useState({
    id: "",
    name: "",
    signalCatalogArn: "",
  });

  const api = useContext(ApiContext);

  const fleetIdRef = useRef<HTMLDivElement>(null);
  const displayNameRef = useRef<HTMLDivElement>(null);
  const signalCatalogRef = useRef<HTMLDivElement>(null);

  const fetchData = useCallback(async () => {
    try {
      const cmd = new ListSignalCatalogsCommand();
      const output = await api.client.send(cmd);

      setStatus("finished");
      setOptions(
        (output.signalCatalogs || []).map((signalCatalog) => ({
          label: signalCatalog.name,
          value: signalCatalog.arn,
        })),
      );
    } catch (error) {
      setStatus("error");
    }
  }, [api.client]);

  const handleLoadItems = useCallback(
    ({ detail: {} }) => {
      setStatus("loading");
      fetchData();
    },
    [fetchData],
  );

  const validateFleetId = (id: string): string => {
    if (!id.trim()) {
      return "Fleet Id is required.";
    }
    const regex = /^[A-Za-z0-9_-]+$/;
    if (!regex.test(id)) {
      return "Invalid characters. Valid characters are letters, numbers, underscores, and hyphens.";
    }
    return "";
  };

  const validateDisplayName = (name: string): string => {
    if (!name.trim()) {
      return "Display Name is required.";
    }
    return "";
  };

  const validateSignalCatalogArn = (arn: string): string => {
    if (!arn || !arn.trim()) {
      return "A signal catalog must be selected.";
    }
    return "";
  };

  const validateAllFields = (): boolean => {
    const idError = validateFleetId(inputData.id || "");
    const nameError = validateDisplayName(inputData.name || "");
    const arnError = validateSignalCatalogArn(inputData.signalCatalogArn || "");

    const newErrors = {
      id: idError,
      name: nameError,
      signalCatalogArn: arnError,
    };

    setErrors(newErrors);

    if (idError) {
      fleetIdRef.current?.scrollIntoView({
        behavior: "smooth",
        block: "center",
      });
      return false;
    }
    if (nameError) {
      displayNameRef.current?.scrollIntoView({
        behavior: "smooth",
        block: "center",
      });
      return false;
    }
    if (arnError) {
      signalCatalogRef.current?.scrollIntoView({
        behavior: "smooth",
        block: "center",
      });
      return false;
    }
    return true;
  };

  useImperativeHandle(ref, () => ({
    validate: validateAllFields,
  }));

  return (
    <Container id="origin-panel" className="custom-screenshot-hide">
      <SpaceBetween size="l">
        <div ref={fleetIdRef}>
          <FormField
            label="Fleet Id"
            description="A unique identifier for the fleet."
            constraintText="Valid characters are a-z, A-Z, 0-9, underscores (_) and hypens (-)."
            i18nStrings={{ errorIconAriaLabel: "Error" }}
            errorText={errors.id}
          >
            <Input
              ariaRequired={true}
              value={inputData.id ?? ""}
              onChange={({ detail: { value } }) => {
                setInputData({ id: value });
                setErrors((prev) => ({ ...prev, id: validateFleetId(value) }));
              }}
              onBlur={() => {
                const id = inputData.id || "";
                setErrors((prev) => ({
                  ...prev,
                  id: validateFleetId(id),
                }));
              }}
            />
          </FormField>
        </div>

        <div ref={displayNameRef}>
          <FormField
            label="Display Name"
            description="A descriptive display name for the fleet."
            i18nStrings={{ errorIconAriaLabel: "Error" }}
            errorText={errors.name}
          >
            <Input
              ariaRequired={true}
              value={inputData.name ?? ""}
              onChange={({ detail: { value } }) => {
                setInputData({ name: value });
                setErrors((prev) => ({
                  ...prev,
                  name: validateDisplayName(value),
                }));
              }}
              onBlur={() => {
                const displayName = inputData.name || "";
                setErrors((prev) => ({
                  ...prev,
                  name: validateDisplayName(displayName),
                }));
              }}
            />
          </FormField>
        </div>

        <FormField
          label="Description"
          i18nStrings={{ errorIconAriaLabel: "Error" }}
        >
          <Textarea
            placeholder="Enter description"
            value={inputData.description ?? ""}
            onChange={({ detail: { value } }) => {
              setInputData({ description: value });
            }}
          />
        </FormField>

        <div ref={signalCatalogRef}>
          <FormField
            label="Signal Catalog ARN"
            info={
              <InfoLink
                id="content-origin-info-link"
                onFollow={() => loadHelpPanelContent(5)}
              />
            }
            description="The Amazon Resource Name (ARN) of a signal catalog."
            i18nStrings={{ errorIconAriaLabel: "Error" }}
            errorText={errors.signalCatalogArn}
          >
            <Select
              options={options}
              selectedOption={selectedOption ?? null}
              selectedAriaLabel="Selected"
              statusType={status}
              placeholder="Choose a signal catalog."
              loadingText="Loading signal catalogs"
              recoveryText="Retry"
              empty="No signal catalogs"
              ariaRequired={true}
              onChange={({ detail: { selectedOption } }) => {
                setInputData({ signalCatalogArn: selectedOption.value });
                setSelectedOption(selectedOption);
                setErrors((prev) => ({
                  ...prev,
                  signalCatalogArn: validateSignalCatalogArn(
                    selectedOption.value,
                  ),
                }));
              }}
              onBlur={() => {
                const arn = inputData.signalCatalogArn || "";
                setErrors((prev) => ({
                  ...prev,
                  signalCatalogArn: validateSignalCatalogArn(arn),
                }));
              }}
              onLoadItems={handleLoadItems}
            />
          </FormField>
        </div>
      </SpaceBetween>
    </Container>
  );
});
