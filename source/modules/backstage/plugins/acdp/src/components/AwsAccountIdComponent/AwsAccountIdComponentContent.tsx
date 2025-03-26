// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React, { useState } from "react";
import { FieldExtensionComponentProps } from "@backstage/plugin-scaffolder-react";
import FormControl from "@material-ui/core/FormControl";
import FormHelperText from "@material-ui/core/FormHelperText";
import InputLabel from "@material-ui/core/InputLabel";
import Select from "@material-ui/core/Select";
import { MenuItem } from "@material-ui/core";
import { AvailableAccountsProps } from "backstage-plugin-acdp-common";
import { useApi } from "@backstage/core-plugin-api";
import { acdpAccountDirectoryApiRef } from "../../api/AcdpAccountDirectoryApi";
import { useQuery } from "@tanstack/react-query";

export const AwsAccountIdComponentContent = ({
  rawErrors,
  required,
  formData,
  onChange,
}: FieldExtensionComponentProps<string>) => {
  const api = useApi(acdpAccountDirectoryApiRef);
  const [availableAccounts, setAvailableAccounts] = useState(
    Array<AvailableAccountsProps>,
  );
  const [targetAccount, setTargetAccount] = useState("");

  const handleAccountChange = (
    event: React.ChangeEvent<{ value: unknown }>,
  ) => {
    setTargetAccount(event.target.value as string);
    onChange(event.target.value as string);
  };

  useQuery({
    queryKey: ["getAvailableAccounts"],
    queryFn: async () => {
      const availableAccountsResponse = await api.getAvailableAccounts();
      if (!availableAccountsResponse)
        throw new Error("No Accounts available for deployment");

      setAvailableAccounts(availableAccountsResponse);
      return availableAccountsResponse;
    },
    enabled: true,
  });

  return (
    <FormControl
      margin="normal"
      required={required}
      error={rawErrors?.length > 0 && !formData}
    >
      <InputLabel htmlFor="targetAwsAccountId" shrink>
        Deployment Target AWS Account ID
      </InputLabel>
      <Select
        labelId="target-aws-account-id-select-label"
        id="target-aws-account-id-select"
        value={targetAccount}
        data-testid="targetAwsAccountIdSelectComponenet"
        onChange={handleAccountChange}
      >
        {availableAccounts.map((data: AvailableAccountsProps) => (
          <MenuItem
            key={data.awsAccountId}
            value={data.awsAccountId}
          >{`${data.alias}: ${data.awsAccountId}`}</MenuItem>
        ))}
      </Select>
      <FormHelperText id="awsAccountIdHelperText">
        Select an AWS Account from the list
      </FormHelperText>
    </FormControl>
  );
};
