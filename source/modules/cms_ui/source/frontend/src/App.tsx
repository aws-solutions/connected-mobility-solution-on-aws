// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import "./App.css";
import { Navigate, Route, Routes, useNavigate } from "react-router-dom";
import {
  Alert,
  AppLayout,
  TopNavigation,
  Spinner,
  ButtonDropdownProps,
} from "@cloudscape-design/components";
import DashboardView from "./components/dashboard/DashboardView";
import {
  APP_TRADEMARK_NAME,
  IG_ROOT,
  IG_URLS,
  FEEDBACK_ISSUES_URL,
  UI_ROUTES,
} from "./utils/constants";
import { useCreateReducer } from "./hooks/useCreateReducer";
import { initialState, insertRuntimeConfig } from "./contexts/home.state";
import { HomeContextProvider } from "./contexts/home.context";
import { useEffect, useContext } from "react";
import { AuthContext } from "react-oauth2-code-pkce";
import MaintenanceAlertsView from "./components/alerts/maintenance/MaintenanceAlertsView";
import FleetManagementView from "./components/fleets/fleet-management/FleetManagementView";
import VehicleManagementView from "./components/vehicles/vehicle-management/VehicleManagementView";
import CampaignManagementView from "./components/campaigns/campaign-management/CampaignManagementView";
import { UserContext } from "./components/commons/UserContext";
import FleetVehiclesMapView from "./components/fleets/vehicle-map/FleetVehicleMapView";
import { CreateFleetPage } from "./components/fleets/create-fleet/CreateFleetPage";
import { EditFleetPage } from "./components/fleets/edit-fleet/EditFleetPage";
import { EditVehiclePage } from "./components/vehicles/edit-vehicle/EditVehiclePage";
import { AssociateVehiclesPage } from "./components/fleets/associate-vehicles/AssociateVehiclesPage";
import { I18nProvider } from "@cloudscape-design/components/i18n";
import enMessages from "@cloudscape-design/components/i18n/messages/all.en.json";
import { CreateVehicleWizard } from "./components/vehicles/create-vehicle-wizard/root";

function App({ runtimeConfig }: Record<string, any>) {
  const initStateWithConfig = insertRuntimeConfig(initialState, runtimeConfig);
  const auth = useContext(AuthContext);

  const uc = useContext(UserContext);

  useEffect(() => {
    uc.theme.applyInitialTheme();
    uc.demoMode.setIsDemoMode(runtimeConfig.isDemoMode == "true");
  }, []);

  const initState = sessionStorage.getItem("init-state")
    ? JSON.parse(sessionStorage.getItem("init-state")!)
    : initStateWithConfig;

  const contextValue = useCreateReducer({
    initialState: initState,
  });

  //must be here to make breadcrumbs work
  useNavigate();

  useEffect(() => {
    if (!auth.loginInProgress && auth.error != undefined) auth.logIn();
  }, [auth.error]);

  const onSignout = async () => {
    sessionStorage.removeItem("init-state");
    localStorage.removeItem("Preferences");

    auth.logOut();
  };

  const profileActions: ButtonDropdownProps.Items = [
    // { id: 'profile', text: 'Profile' },
    { id: "preferences", text: "Preferences" },
    { id: "switchTheme", text: "Switch Theme" },
    // { id: 'security', text: 'Security' },
    {
      id: "support-group",
      text: "Support",
      items: [
        {
          id: "documentation",
          text: "Documentation",
          href: IG_ROOT,
          external: true,
          externalIconAriaLabel: " (opens in new tab)",
        },
        {
          id: "feedback",
          text: "Feedback",
          href: FEEDBACK_ISSUES_URL,
          external: true,
          externalIconAriaLabel: " (opens in new tab)",
        },
        {
          id: "support",
          text: "Customer support",
          href: IG_URLS.SUPPORT,
          external: true,
          externalIconAriaLabel: " (opens in new tab)",
        },
      ],
    },
    {
      id: "signout",
      text: "Sign out",
      ariaLabel: "Sign out",
      iconName: "lock-private",
    },
  ];

  const onProfileFollow = (
    event: CustomEvent<ButtonDropdownProps.ItemClickDetails>,
  ) => {
    if (event.detail.id === "signout") {
      onSignout();
    }
    if (event.detail.id === "switchTheme") {
      uc.theme.switchThemeMode();
    }
  };

  return (
    <>
      <HomeContextProvider
        value={{
          ...contextValue,
        }}
      >
        <div className="top-navbar">
          <TopNavigation
            identity={{
              href: UI_ROUTES.ROOT,
              title: APP_TRADEMARK_NAME,
            }}
            utilities={[
              {
                type: "menu-dropdown",
                text: auth.tokenData?.username,
                description: auth.idTokenData?.email,
                iconName: "user-profile",
                items: profileActions,
                onItemClick: onProfileFollow,
              },
            ]}
            i18nStrings={{
              overflowMenuTriggerText: "More",
              overflowMenuTitleText: "All",
              searchIconAriaLabel: "Search",
              searchDismissIconAriaLabel: "Close search",
            }}
          />
        </div>
        {auth.tokenData?.username ? (
          <I18nProvider locale="en" messages={[enMessages]}>
            <AppLayout
              contentType="dashboard"
              disableContentPaddings
              toolsHide
              navigationHide
              content={
                <div className="flex flex-1">
                  <Routes>
                    <Route path={UI_ROUTES.ROOT} element={<DashboardView />} />
                    <Route
                      path={UI_ROUTES.FLEET_MANAGEMENT}
                      element={<FleetManagementView />}
                    />
                    <Route
                      path={UI_ROUTES.FLEET_VEHICLES_MAP}
                      element={<FleetVehiclesMapView />}
                    />
                    <Route
                      path={UI_ROUTES.FLEET_CREATE}
                      element={<CreateFleetPage />}
                    />
                    <Route
                      path={UI_ROUTES.FLEET_EDIT}
                      element={<EditFleetPage />}
                    />
                    <Route
                      path={UI_ROUTES.FLEET_ASSOCIATE_VEHICLES}
                      element={<AssociateVehiclesPage />}
                    />
                    <Route
                      path={UI_ROUTES.VEHICLE_MANAGEMENT}
                      element={<VehicleManagementView />}
                    />
                    <Route
                      path={UI_ROUTES.VEHICLE_CREATE}
                      element={<CreateVehicleWizard />}
                    />
                    <Route
                      path={UI_ROUTES.VEHICLE_EDIT}
                      element={<EditVehiclePage />}
                    />
                    <Route
                      path={UI_ROUTES.CAMPAIGN_MANAGEMENT}
                      element={<CampaignManagementView />}
                    />
                    <Route
                      path={UI_ROUTES.ALERTS_MAINTENANCE}
                      element={<MaintenanceAlertsView />}
                    />
                    <Route path="*" element={<Navigate to="/" />} />
                  </Routes>
                </div>
              }
            />
          </I18nProvider>
        ) : auth.loginInProgress ? (
          <>
            <Spinner size="large" />
            <div>Logging In...</div>
          </>
        ) : (
          <div>
            <Alert
              statusIconAriaLabel="Error"
              type="error"
              header="Unable to access data. Please sign in and ensure you have proper access and correct credentials."
            ></Alert>
          </div>
        )}
      </HomeContextProvider>
    </>
  );
}

export default App;
