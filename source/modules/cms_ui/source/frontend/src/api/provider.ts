// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { FleetManagementClient } from "@com.cms.fleetmanagement/api-client";
import React, { createContext, useMemo, ReactNode, useContext } from "react";
import { createFleetManagementClient } from "./client";
import { AuthContext } from "react-oauth2-code-pkce";

export interface ApiConfig {
  baseUrl: string;
  isDemoMode: "true" | "false";
}

export interface ApiContextValue {
  config: ApiConfig;
  token: string;
  client: FleetManagementClient;
}

export const ApiContext = createContext<ApiContextValue>({
  config: { baseUrl: "http://localhost", isDemoMode: "true" },
  token: "",
  client: createFleetManagementClient(
    { baseUrl: "http://localhost", isDemoMode: "true" },
    "",
  ),
});

interface ApiProviderProps {
  children: ReactNode;
  apiConfig: ApiConfig;
  token: string;
}

interface ApiProviderWithAuthProps {
  children: ReactNode;
  apiConfig: ApiConfig;
}

export const ApiProviderWithAuth = ({
  children,
  apiConfig,
}: ApiProviderWithAuthProps) => {
  const auth = useContext(AuthContext);
  return React.createElement(ApiProvider, {
    children: children,
    apiConfig: apiConfig,
    token: auth.token,
  });
};

export const ApiProvider = ({
  children,
  apiConfig,
  token,
}: ApiProviderProps) => {
  const apiValue = useMemo<ApiContextValue>(
    () => ({
      config: apiConfig,
      token,
      client: createFleetManagementClient(apiConfig, token),
    }),
    [apiConfig, token],
  );

  return React.createElement(
    ApiContext.Provider,
    { value: apiValue },
    children,
  );
};
