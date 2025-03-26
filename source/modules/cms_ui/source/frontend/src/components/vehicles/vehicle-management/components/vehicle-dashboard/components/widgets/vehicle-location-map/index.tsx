// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React, { useContext, useEffect, useState } from "react";
import { Box, Header, Link } from "@cloudscape-design/components";
import { WidgetConfig } from "../interfaces";
import { useNavigate } from "react-router-dom";
import { UI_ROUTES } from "@/utils/constants";
import { VehicleItem } from "@com.cms.fleetmanagement/api-client";
import { VehicleManagementContext } from "@/components/vehicles/vehicle-management/VehicleManagementContext";
import Map, { NavigationControl, ViewState } from "react-map-gl/maplibre";
import { Mode } from "@cloudscape-design/global-styles";
import "maplibre-gl/dist/maplibre-gl.css";
import PositionLayer from "./PositionLayer";
import { UserContext } from "@/components/commons/UserContext";
import {
  MapAuthHelper,
  withIdentityPoolId,
} from "@aws/amazon-location-utilities-auth-helper";
import { AuthContext } from "react-oauth2-code-pkce";
import HomeContext from "@/contexts";

export const vehicleLocationMap: WidgetConfig = {
  definition: { defaultRowSpan: 4, defaultColumnSpan: 2 },
  data: {
    icon: "table",
    title: "Vehicle Location Map",
    description: "View current vehicle location",
    disableContentPaddings: false,
    header: WidgetHeader,
    content: WidgetContent,
    footer: WidgetFooter,
  },
};

function WidgetHeader() {
  return <Header>Vehicle Location</Header>;
}

function WidgetFooter() {
  const navigate = useNavigate();

  return (
    <Box textAlign="center">
      <Link
        onClick={() => navigate(UI_ROUTES.ROOT)} //TODO
        variant="primary"
      >
        View full screen map
      </Link>
    </Box>
  );
}

let isSubscribed = true;
async function update(
  locationVehicle: VehicleItem | undefined,
  setData: React.Dispatch<React.SetStateAction<any | undefined>>,
  setDataStatus: React.Dispatch<
    React.SetStateAction<"loading" | "finished" | "error">
  >,
  setViewState: React.Dispatch<React.SetStateAction<Partial<ViewState>>>,
) {
  if (locationVehicle) {
    isSubscribed = true;
    setDataStatus("loading");

    try {
      const vehicleLocationData = {
        id: locationVehicle.name,
        current: {
          longitude: "-95.4304869",
          latitude: "29.9356254",
          timestamp: new Date(),
        },
        historical: [
          {
            longitude: "-95.4304869",
            latitude: "29.9356254",
            timestamp: new Date(),
          },
        ],
      };

      if (isSubscribed) {
        setData(vehicleLocationData);
        setViewState({
          longitude: Number(vehicleLocationData.current.longitude),
          latitude: Number(vehicleLocationData.current.latitude),
        });
      }
      setDataStatus("finished");
    } catch (e) {
      setDataStatus("error");
    }
  } else {
    setDataStatus("error");
  }

  return () => (isSubscribed = false);
}

export default function WidgetContent() {
  const [data, setData] = useState<any | undefined>(undefined);
  const [authHelper, setAuthHelper] = useState<MapAuthHelper | undefined>(
    undefined,
  );
  const [mapTheme, setMapTheme] = useState<"Light" | "Dark">("Light");
  const [viewState, setViewState] = React.useState<Partial<ViewState>>({
    longitude: 0,
    latitude: 0,
  });
  const [dataStatus, setDataStatus] = useState<
    "loading" | "finished" | "error"
  >("loading");

  const vmc = useContext(VehicleManagementContext);
  const uc = useContext(UserContext);
  const authContext = useContext(AuthContext);
  const homeContext = useContext(HomeContext);

  const runtimeConfig = homeContext.state.runtimeConfig;

  useEffect(() => {
    update(vmc.vehicle.locationVehicle, setData, setDataStatus, setViewState);
  }, [vmc.vehicle.locationVehicle]);

  useEffect(() => {
    withIdentityPoolId(runtimeConfig.mapAuth.identityPoolId, {
      logins: {
        [runtimeConfig.mapAuth.identityPoolClient]: authContext.idToken ?? "",
      },
    }).then((authHelper) => {
      setAuthHelper(authHelper);
    });
    update(vmc.vehicle.locationVehicle, setData, setDataStatus, setViewState);
  }, []);

  useEffect(() => {
    switch (uc.theme.currentThemeMode) {
      case Mode.Dark:
        setMapTheme("Dark");
        break;
      case Mode.Light:
      default:
        setMapTheme("Light");
    }
  }, [uc.theme.currentThemeMode]);

  return authHelper == undefined ? (
    <>Loading...</>
  ) : (
    <Map
      id="map-view"
      {...viewState}
      initialViewState={{
        zoom: 15,
      }}
      mapStyle={`https://maps.geo.${runtimeConfig.awsRegion}.amazonaws.com/maps/v0/maps/${runtimeConfig.mapAuth.mapName}/style-descriptor?color-scheme=${mapTheme}`}
      maxZoom={16}
      dragPan={false}
      dragRotate={false}
      touchZoomRotate={false}
      touchPitch={false}
      attributionControl={false}
      {...authHelper.getMapAuthenticationOptions()}
    >
      <NavigationControl position="top-left" showCompass={false} />
      <PositionLayer data={data}></PositionLayer>
    </Map>
  );
}
