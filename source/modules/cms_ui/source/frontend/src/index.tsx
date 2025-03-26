// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import "@cloudscape-design/global-styles/index.css";

import { Mode, applyMode } from "@cloudscape-design/global-styles";

import React, { useState, useRef } from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import { AuthProvider } from "react-oauth2-code-pkce";
import { SessionExpiredModal } from "./components/commons/session-expired-modal";
import {
  TAuthConfig,
  TRefreshTokenExpiredEvent,
} from "react-oauth2-code-pkce/dist/types";
import { UserContextProvider } from "./components/commons/UserContext";
import { ApiProviderWithAuth, ApiConfig } from "./api/provider";

// apply a color mode
applyMode(Mode.Light);

export async function getRuntimeConfig() {
  const runtimeConfig = await fetch("/runtimeConfig.json");
  return runtimeConfig.json();
}

getRuntimeConfig().then(function (config) {
  const runtimeConfig = config;

  //TODO: Read from config.json or dynamically

  const loginRedirectPathName = "callback";
  const loginRedirectUri = `${window.location.origin}/${loginRedirectPathName}`;
  runtimeConfig.oAuth.loginRedirectPathName = `/${loginRedirectPathName}`;

  const root = ReactDOM.createRoot(document.getElementById("root") as any);

  function Main() {
    const [showSessionExpiredModal, setShowSessionExpiredModal] =
      useState(false);
    const refreshTokenExpireEventRef = useRef<TRefreshTokenExpiredEvent | null>(
      null,
    );
    // const refreshTokenExpireEventRef = useRef<MutableRefObject<(() => void)>(null);

    const handleSessionRefresh = () => {
      setShowSessionExpiredModal(false);
      if (refreshTokenExpireEventRef.current)
        refreshTokenExpireEventRef.current.logIn();
    };

    const authConfig: TAuthConfig = {
      clientId: runtimeConfig.oAuth.clientId,
      authorizationEndpoint: runtimeConfig.oAuth.authorizationEndpoint,
      tokenEndpoint: runtimeConfig.oAuth.tokenEndpoint,
      redirectUri: loginRedirectUri,
      clearURL: true,
      scope: runtimeConfig.oAuth.scopes,
      autoLogin: true,
      decodeToken: true,
      logoutEndpoint: runtimeConfig.oAuth.logoutEndpoint,
      extraLogoutParameters: {
        redirect_uri: loginRedirectUri,
        response_type: "code",
      },
      refreshTokenExpiresIn: 10 * 24 * 60 * 60, //Default to 10 days in seconds
      onRefreshTokenExpire: (event: TRefreshTokenExpiredEvent) => {
        refreshTokenExpireEventRef.current = event;
        setShowSessionExpiredModal(true);
      },
      preLogin: () => {
        let currentPath = window.location.pathname;
        if (window.location.hash) currentPath += `/${window.location.hash}`;
        return localStorage.setItem("preLoginPath", currentPath);
      },
      postLogin: () =>
        window.location.replace(localStorage.getItem("preLoginPath") || ""),
    };

    const apiConfig: ApiConfig = {
      baseUrl: runtimeConfig.apiEndpoint,
      isDemoMode: runtimeConfig.isDemoMode,
    };

    return (
      <AuthProvider authConfig={authConfig}>
        <ApiProviderWithAuth apiConfig={apiConfig}>
          <BrowserRouter>
            <UserContextProvider>
              <App runtimeConfig={runtimeConfig} />
              <SessionExpiredModal
                visible={showSessionExpiredModal}
                onRefresh={handleSessionRefresh}
              />
            </UserContextProvider>
          </BrowserRouter>
        </ApiProviderWithAuth>
      </AuthProvider>
    );
  }

  root.render(
    <React.StrictMode>
      <Main />
    </React.StrictMode>,
  );
});
