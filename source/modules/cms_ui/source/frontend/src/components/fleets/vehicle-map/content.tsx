// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React, {
  SetStateAction,
  useContext,
  useEffect,
  useRef,
  useState,
} from "react";
import {
  Button,
  Select,
  SpaceBetween,
  FormField,
  AppLayout,
  SplitPanel,
  Container,
  Cards,
  Box,
  Modal,
  AppLayoutProps,
  StatusIndicator,
} from "@cloudscape-design/components";
import { PageBanner } from "@/components/dashboard/components/page-banner";
import { UserContext } from "@/components/commons/UserContext";
import { FleetSelectionItem } from "@/components/commons/fleet-selection";
import Map, {
  NavigationControl,
  Marker,
  Source,
  Layer,
  MapRef,
  LngLatBoundsLike,
} from "react-map-gl/maplibre";
import {
  MapAuthHelper,
  withIdentityPoolId,
} from "@aws/amazon-location-utilities-auth-helper";
import HomeContext from "@/contexts";
import { AuthContext } from "react-oauth2-code-pkce";
import { Mode } from "@cloudscape-design/global-styles";
import { FleetVehiclesMapHeader, FleetVehiclesMapInfo } from "./header";
import { useSplitPanel } from "@/components/commons/split-panel";
import { useCollection } from "@cloudscape-design/collection-hooks";
import {
  DetailedVehicleInfo,
  VEHICLE_STATUS,
  Vehicle,
  VehicleRouteFile,
  Coordinate,
} from "./interfaces";
import {
  CARD_DEFINITION_SELECTED,
  CARD_DEFINITIONS,
} from "./components/cards-config";
import { Breadcrumbs } from "../../commons/breadcrumbs";
import driverDetails from "./data/driverDetails.json";
import vehicleDetails from "./data/vehicleDetails.json";
import { UI_ROUTES } from "@/utils/constants";
import { Navigation } from "@/components/commons";

interface ContentProps {}

const NUMBER_OF_VEHICLES = 100;
const RATE = 1000;

export function Content({}: ContentProps) {
  const uc = useContext(UserContext);
  const homeContext = useContext(HomeContext);
  const authContext = useContext(AuthContext);
  const runtimeConfig = homeContext.state.runtimeConfig;

  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [detailedVehicleInfos, setDetailedVehicleInfos] = useState<
    DetailedVehicleInfo[]
  >([]);
  const [selectedFilter, setSelectedFilter] = useState<VEHICLE_STATUS | "ALL">(
    "ALL",
  );

  const { items, actions, collectionProps } = useCollection(
    detailedVehicleInfos,
    {
      filtering: {
        empty: <Box textAlign="center">No fleet vehicles on Map</Box>,
      },
      selection: {},
    },
  );
  const {
    splitPanelOpen,
    onSplitPanelToggle,
    splitPanelSize,
    onSplitPanelResize,
  } = useSplitPanel(collectionProps.selectedItems, true, 300);

  const [refreshInProgress, setRefreshInProgress] = useState(false);
  const [selectedVehicleIndex, setSelectedVehicleIndex] = useState<
    number | null
  >(null);
  const [selectedVehicle, setSelectedVehicle] = useState<Vehicle | null>(null);
  const [previousViewState, setPreviousViewState] = useState<{
    longitude: number;
    latitude: number;
    zoom: number;
  } | null>(null);

  const [mapTheme, setMapTheme] = useState<"Light" | "Dark">("Light");
  const [authHelper, setAuthHelper] = useState<MapAuthHelper>();
  const [mapIsLoaded, setMapIsLoaded] = useState(false);
  const [vehiclesAreReady, setVehiclesAreReady] = useState(false);

  const mapRef = useRef<MapRef>(null);

  const animationSpeed = 5000;
  const lastInfoUpdateRef = useRef<number>(0);

  const [selectedEvent, setSelectedEvent] = useState<{
    vehicleId: string;
    eventIndex: number;
    title: string;
    timestamp: number;
  } | null>(null);

  const [hoveredVehicleId, setHoveredVehicleId] = useState<string | null>(null);
  const [hoveredEvent, setHoveredEvent] = useState<{
    vehicleId: string;
    eventIndex: number;
  } | null>(null);

  const getBoundsForCoordinates = (
    coords: Coordinate[],
  ): LngLatBoundsLike | null => {
    if (!coords.length) return null;
    const lats = coords.map((c) => c.latitude);
    const longs = coords.map((c) => c.longitude);
    const minLat = Math.min(...lats);
    const maxLat = Math.max(...lats);
    const minLon = Math.min(...longs);
    const maxLon = Math.max(...longs);
    return [minLon, minLat, maxLon, maxLat];
  };

  useEffect(() => {
    const now = Date.now();
    if (now - lastInfoUpdateRef.current < animationSpeed) {
      return;
    }
    lastInfoUpdateRef.current = now;

    const updatedInfos = vehicles.map<DetailedVehicleInfo>((vehicle) => ({
      id: vehicle.vehicleId,
      vehicle,
      vehicleDetails: vehicleDetails[vehicle.vehicleId],
      driverDetails: driverDetails[vehicle.driverId],
      filteredRecordedEvents: vehicle.recordedEvents.filter((event) =>
        isEventOnTraveledPath(vehicle, event),
      ),
      startTime: vehicle.startTime,
    }));
    setDetailedVehicleInfos(updatedInfos);
  }, [vehicles, animationSpeed]);

  useEffect(() => {
    withIdentityPoolId(runtimeConfig.mapAuth.identityPoolId, {
      logins: {
        [runtimeConfig.mapAuth.identityPoolClient]: authContext.idToken ?? "",
      },
    }).then(setAuthHelper);

    initializeVehiclesFromRoutes();
  }, []);

  useEffect(() => {
    setMapTheme(uc.theme.currentThemeMode === Mode.Dark ? "Dark" : "Light");
  }, [uc.theme.currentThemeMode]);

  useEffect(() => {
    if (mapIsLoaded && vehiclesAreReady) {
      fitAllVehicles();
    }
  }, [mapIsLoaded, vehiclesAreReady]);

  const fitAllVehicles = () => {
    if (!mapRef.current) return;
    const allPositions = vehicles.map((v) => v.route.vehiclePosition);
    const bounds = getBoundsForCoordinates(allPositions);
    if (bounds) {
      mapRef.current.fitBounds(bounds, { padding: 50, duration: 2000 });
    }
  };

  const initializeVehiclesFromRoutes = () => {
    setRefreshInProgress(true);
    setTimeout(async () => {
      const routePromises = [];
      for (let i = 0; i < NUMBER_OF_VEHICLES; i++) {
        routePromises.push(
          import(`./routes/vehicle_${i}.json`).then(
            (mod) => mod.default as VehicleRouteFile,
          ),
        );
      }
      const allRoutes = await Promise.all(routePromises);

      const newVehicles: Vehicle[] = allRoutes.map<Vehicle>((v) => {
        const coords =
          v.data.routes[0]?.geometry?.coordinates.map(([lon, lat]) => ({
            latitude: lat,
            longitude: lon,
          })) || [];
        const recordedEvents = v.recordedEvents || [];

        const routeLength = coords.length;
        let currentIndex = 0;
        let traveledPath: Coordinate[] = [];
        let vehiclePosition = v.warehouse;
        let startTime = Date.now() - currentIndex * RATE;

        if (routeLength > 0) {
          const mid = Math.round(routeLength / 2);
          currentIndex = mid;
          traveledPath = coords.slice(0, currentIndex + 1);
          vehiclePosition = coords[currentIndex];
          startTime = Date.now() - currentIndex * RATE;
        }

        return {
          route: {
            routeCoordinates: coords,
            traveledPath,
            vehiclePosition,
            currentIndex,
            stepIndex: 0,
            warehouse: v.warehouse,
          },
          recordedEvents: recordedEvents,
          details: `Vehicle ${v.vehicleIndex} is currently at ${vehiclePosition.latitude}, ${vehiclePosition.longitude}`,
          driverId: `driver_${
            v.vehicleIndex % Object.keys(driverDetails).length
          }`,
          vehicleId: `vehicle_${v.vehicleIndex}`,
          startTime,
        };
      });

      setVehicles(newVehicles);
      animateVehicles(newVehicles);
      setVehiclesAreReady(true);
      setRefreshInProgress(false);
    }, 2000);
  };

  const animateVehicles = (vehiclesArray: Vehicle[]) => {
    const stepCount = 500;
    const animateStep = () => {
      setVehicles((prev) =>
        prev.map((veh) => {
          const { routeCoordinates, currentIndex, stepIndex, traveledPath } =
            veh.route;
          if (
            routeCoordinates.length < 2 ||
            currentIndex >= routeCoordinates.length - 1
          ) {
            return veh;
          }
          const start = routeCoordinates[currentIndex];
          const end = routeCoordinates[currentIndex + 1];
          const t = stepIndex / stepCount;
          const currentPosition = {
            latitude: start.latitude + t * (end.latitude - start.latitude),
            longitude: start.longitude + t * (end.longitude - start.longitude),
          };
          let newCurrentIndex = currentIndex;
          let newStepIndex = stepIndex;
          let newTraveledPath = traveledPath;
          if (stepIndex === stepCount) {
            newCurrentIndex++;
            newStepIndex = 0;
            newTraveledPath = [...traveledPath, end];
          } else {
            newStepIndex++;
          }
          return {
            ...veh,
            route: {
              ...veh.route,
              vehiclePosition: currentPosition,
              traveledPath: newTraveledPath,
              currentIndex: newCurrentIndex,
              stepIndex: newStepIndex,
            },
          };
        }),
      );

      const stillMoving = vehiclesArray.some(
        (v) => v.route.currentIndex < v.route.routeCoordinates.length - 1,
      );
      if (stillMoving) {
        setTimeout(animateStep, animationSpeed / stepCount);
      }
    };
    animateStep();
  };

  const handleVehicleClick = (idx: number) => {
    if (selectedVehicleIndex === idx) {
      setSelectedVehicleIndex(null);
      setSelectedVehicle(null);
      if (previousViewState && mapRef.current) {
        mapRef.current.flyTo({
          center: [previousViewState.longitude, previousViewState.latitude],
          zoom: previousViewState.zoom,
          duration: 1000,
        });
      }
    } else {
      if (mapRef.current) {
        const center = mapRef.current.getCenter();
        const zoom = mapRef.current.getZoom();
        setPreviousViewState({
          longitude: center.lng,
          latitude: center.lat,
          zoom,
        });
      }
      setSelectedVehicleIndex(idx);
      setSelectedVehicle(vehicles[idx]);
      const coords = vehicles[idx].route.routeCoordinates;
      const bounds = getBoundsForCoordinates(coords);
      if (bounds && mapRef.current) {
        mapRef.current.fitBounds(bounds, { padding: 50, duration: 2000 });
      }
    }
  };

  const handleEventClick = (
    vehicleId: string,
    eventIndex: number,
    event: any,
  ) => {
    setSelectedEvent({
      vehicleId,
      eventIndex,
      title: event.title,
      timestamp:
        vehicles.find((x) => x.vehicleId === vehicleId)?.startTime +
        event.timestamp,
    });
  };

  const filteredItems = detailedVehicleInfos.filter((info) => {
    if (selectedFilter === "ALL") return true;
    return info.vehicleDetails.status === selectedFilter;
  });

  const filteredVehicles = vehicles.filter((vehicle) => {
    const info = detailedVehicleInfos.find(
      (dvi) => dvi.vehicle.vehicleId === vehicle.vehicleId,
    );
    if (!info) return false;
    if (selectedFilter === "ALL") return true;
    return info.vehicleDetails.status === selectedFilter;
  });

  const initialCenter = {
    latitude: 36.1707237,
    longitude: -115.1682909,
    zoom: 3,
  };

  const selectStatusOptions = [
    { label: "All", value: "ALL" },
    { label: "Healthy", value: "HEALTHY" },
    { label: "Unhealthy", value: "UNHEALTHY" },
  ];

  const selectedStatusOption =
    selectStatusOptions.find((option) => option.value === selectedFilter) ||
    selectStatusOptions[0];

  const handleStatusChange = (event: any) => {
    const newValue = event.detail.selectedOption.value as
      | VEHICLE_STATUS
      | "ALL";
    setSelectedFilter(newValue);
    actions.setSelectedItems([]);
    setSelectedVehicleIndex(null);
    setSelectedVehicle(null);

    if (mapRef.current) {
      const relevant = vehicles.filter((v) => {
        const info = detailedVehicleInfos.find(
          (d) => d.vehicle.vehicleId === v.vehicleId,
        );
        if (!info) return false;
        if (newValue === "ALL") return true;
        return info.vehicleDetails.status === newValue;
      });
      const positions = relevant.map((r) => r.route.vehiclePosition);
      const bounds = getBoundsForCoordinates(positions);
      if (bounds) {
        mapRef.current.fitBounds(bounds, { padding: 50, duration: 2000 });
      }
    }
  };

  const handleRefreshClick = () => {
    setRefreshInProgress(true);
    setSelectedVehicleIndex(null);
    setSelectedVehicle(null);
    setPreviousViewState(null);

    initializeVehiclesFromRoutes();

    if (mapRef.current) {
      const relevant = vehicles.filter((v) => {
        const info = detailedVehicleInfos.find(
          (d) => d.vehicle.vehicleId === v.vehicleId,
        );
        if (!info) return false;
        if (selectedFilter === "ALL") return true;
        return info.vehicleDetails.status === selectedFilter;
      });
      const positions = relevant.map((r) => r.route.vehiclePosition);
      const bounds = getBoundsForCoordinates(positions);
      if (bounds) {
        mapRef.current.fitBounds(bounds, { padding: 50, duration: 2000 });
      }
    }
  };

  const isEventOnTraveledPath = (vehicle: Vehicle, event: any): boolean => {
    return vehicle.route.traveledPath.some(
      (pathPoint) =>
        pathPoint.latitude === event.latitude &&
        pathPoint.longitude === event.longitude,
    );
  };

  const appLayoutRef = useRef<AppLayoutProps.Ref>();

  const [toolsOpen, setToolsOpen] = useState(false);
  const [toolsContent, setToolsContent] = useState(() => (
    <FleetVehiclesMapInfo />
  ));

  return (
    <AppLayout
      ref={appLayoutRef}
      contentType="dashboard"
      navigation={<Navigation activeHref={UI_ROUTES.FLEET_VEHICLES_MAP} />}
      toolsOpen={toolsOpen}
      tools={toolsContent}
      onToolsChange={({ detail }) => setToolsOpen(detail.open)}
      breadcrumbs={
        <Breadcrumbs
          items={[
            {
              text: "Fleet Vehicles Map",
              href: UI_ROUTES.FLEET_VEHICLES_MAP,
            },
          ]}
        />
      }
      splitPanelOpen={splitPanelOpen}
      onSplitPanelToggle={onSplitPanelToggle}
      splitPanelSize={splitPanelSize}
      onSplitPanelResize={onSplitPanelResize}
      splitPanelPreferences={{ position: "side" }}
      splitPanel={
        <SplitPanel hidePreferencesButton header="Vehicle Details">
          {selectedVehicle === null && (
            <Cards
              {...collectionProps}
              entireCardClickable
              stickyHeader
              cardDefinition={CARD_DEFINITIONS}
              items={filteredItems}
              selectionType="single"
              variant="full-page"
              trackBy="id"
              onSelectionChange={(event) => {
                collectionProps.onSelectionChange?.(event);

                const newlySelectedItems = event.detail.selectedItems;
                if (newlySelectedItems && newlySelectedItems.length > 0) {
                  const selectedInfo = newlySelectedItems[0];
                  const vehicleIndex = vehicles.findIndex(
                    (v) => v.vehicleId === selectedInfo.vehicle.vehicleId,
                  );
                  if (vehicleIndex >= 0) {
                    if (mapRef.current) {
                      const center = mapRef.current.getCenter();
                      const zoom = mapRef.current.getZoom();
                      setPreviousViewState({
                        longitude: center.lng,
                        latitude: center.lat,
                        zoom,
                      });
                    }
                    setSelectedVehicleIndex(vehicleIndex);
                    setSelectedVehicle(vehicles[vehicleIndex]);

                    const coords =
                      vehicles[vehicleIndex].route.routeCoordinates;
                    const bounds = getBoundsForCoordinates(coords);
                    if (bounds && mapRef.current) {
                      mapRef.current.fitBounds(bounds, {
                        padding: 50,
                        duration: 1000,
                      });
                    }
                  }
                } else {
                  setSelectedVehicleIndex(null);
                  setSelectedVehicle(null);
                }
              }}
            />
          )}
          {selectedVehicle !== null && (
            <SpaceBetween size="m" direction="vertical">
              <Cards
                cardDefinition={CARD_DEFINITION_SELECTED}
                items={[
                  detailedVehicleInfos.find(
                    (d) => d.vehicle.vehicleId === selectedVehicle.vehicleId,
                  ),
                ]}
                selectionType="single"
                selectedItems={[
                  detailedVehicleInfos.find(
                    (d) => d.vehicle.vehicleId === selectedVehicle.vehicleId,
                  ),
                ]}
                variant="full-page"
                trackBy="id"
              />
              <Button
                onClick={() => {
                  setSelectedVehicleIndex(null);
                  setSelectedVehicle(null);
                  actions.setSelectedItems([]);
                  if (previousViewState && mapRef.current) {
                    mapRef.current.flyTo({
                      center: [
                        previousViewState.longitude,
                        previousViewState.latitude,
                      ],
                      zoom: previousViewState.zoom,
                      duration: 1000,
                    });
                  }
                }}
              >
                Back
              </Button>
            </SpaceBetween>
          )}
        </SplitPanel>
      }
      content={
        <div
          style={{
            display: "grid",
            gridTemplateRows: "auto 1fr",
            rowGap: "1rem",
            height: "95%",
          }}
        >
          <SpaceBetween size="m">
            <FleetVehiclesMapHeader
              actions={
                <Button
                  iconName="refresh"
                  onClick={handleRefreshClick}
                  disabled={refreshInProgress}
                >
                  Refresh
                </Button>
              }
            />
            <SpaceBetween size="xs" direction="horizontal" alignItems="center">
              <FleetSelectionItem />
              <FormField label="Filter vehicles by status:" />
              <Select
                selectedOption={selectedStatusOption}
                options={selectStatusOptions}
                onChange={handleStatusChange}
              />
            </SpaceBetween>
            <PageBanner />
          </SpaceBetween>
          <Container fitHeight disableContentPaddings disableHeaderPaddings>
            {authHelper ? (
              <>
                <Map
                  ref={mapRef}
                  id="map-view"
                  initialViewState={{
                    zoom: initialCenter.zoom,
                    longitude: initialCenter.longitude,
                    latitude: initialCenter.latitude,
                  }}
                  mapStyle={`https://maps.geo.${runtimeConfig.awsRegion}.amazonaws.com/maps/v0/maps/${runtimeConfig.mapAuth.mapName}/style-descriptor?color-scheme=${mapTheme}`}
                  attributionControl={false}
                  onLoad={() => {
                    setMapIsLoaded(true);
                  }}
                  {...authHelper.getMapAuthenticationOptions()}
                  style={{
                    height: "100%",
                    width: "100%",
                    borderRadius: "16px",
                  }}
                >
                  <NavigationControl position="top-left" showCompass={false} />
                  {filteredVehicles.map((vehicle) => {
                    const isSelected =
                      selectedVehicleIndex !== null &&
                      vehicles[selectedVehicleIndex]?.vehicleId ===
                        vehicle.vehicleId;

                    return (
                      <React.Fragment key={vehicle.vehicleId}>
                        {isSelected &&
                          vehicle.route.traveledPath.length > 0 && (
                            <Source
                              id={`traveled-path-${vehicle.vehicleId}`}
                              type="geojson"
                              data={{
                                type: "Feature",
                                geometry: {
                                  type: "LineString",
                                  coordinates: vehicle.route.traveledPath.map(
                                    (p) => [p.longitude, p.latitude],
                                  ),
                                },
                              }}
                            >
                              <Layer
                                id={`traveled-path-line-${vehicle.vehicleId}`}
                                type="line"
                                paint={{
                                  "line-color": "#00f",
                                  "line-width": 4,
                                }}
                              />
                            </Source>
                          )}

                        <Marker
                          longitude={vehicle.route.vehiclePosition.longitude}
                          latitude={vehicle.route.vehiclePosition.latitude}
                          onClick={() => {
                            const realIndex = vehicles.findIndex(
                              (v) => v.vehicleId === vehicle.vehicleId,
                            );
                            handleVehicleClick(realIndex);
                          }}
                        >
                          <img
                            src="/images/amzn_truck.png"
                            alt={`Vehicle ID: ${vehicle.vehicleId}`}
                            title={`Vehicle ID: ${vehicle.vehicleId}`}
                            style={{
                              width:
                                hoveredVehicleId === vehicle.vehicleId ||
                                selectedVehicle?.vehicleId === vehicle.vehicleId
                                  ? "28px"
                                  : "20px",
                              height:
                                hoveredVehicleId === vehicle.vehicleId ||
                                selectedVehicle?.vehicleId === vehicle.vehicleId
                                  ? "28px"
                                  : "20px",
                              cursor: "pointer",
                              transition: "width 0.2s, height 0.2s",
                            }}
                            onMouseEnter={() =>
                              setHoveredVehicleId(vehicle.vehicleId)
                            }
                            onMouseLeave={() => setHoveredVehicleId(null)}
                          />
                        </Marker>

                        {isSelected &&
                          vehicle.recordedEvents?.map((event, index) => {
                            if (!isEventOnTraveledPath(vehicle, event)) {
                              return null;
                            }

                            const isSelectedEvent =
                              selectedEvent?.vehicleId === vehicle.vehicleId &&
                              selectedEvent?.eventIndex === index;
                            const isHoveredEvent =
                              hoveredEvent?.vehicleId === vehicle.vehicleId &&
                              hoveredEvent?.eventIndex === index;

                            return (
                              <Marker
                                key={`hard-braking-${vehicle.vehicleId}-${index}`}
                                longitude={event.longitude}
                                latitude={event.latitude}
                              >
                                <span
                                  title={`Event: Hard Braking`}
                                  style={{
                                    fontSize:
                                      isSelectedEvent || isHoveredEvent
                                        ? "1.44em"
                                        : "1.2em",
                                    cursor: "pointer",
                                    transition: "font-size 0.2s",
                                  }}
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleEventClick(
                                      vehicle.vehicleId,
                                      index,
                                      event,
                                    );
                                  }}
                                  onMouseEnter={() =>
                                    setHoveredEvent({
                                      vehicleId: vehicle.vehicleId,
                                      eventIndex: index,
                                    })
                                  }
                                  onMouseLeave={() => setHoveredEvent(null)}
                                >
                                  ⚠️
                                </span>
                              </Marker>
                            );
                          })}
                      </React.Fragment>
                    );
                  })}
                </Map>

                {selectedEvent && (
                  <Modal
                    onDismiss={() => setSelectedEvent(null)}
                    visible={true}
                    header={selectedEvent.title}
                    footer={
                      <Button onClick={() => setSelectedEvent(null)}>
                        Close
                      </Button>
                    }
                  >
                    <img
                      src={
                        ["1", "2", "3"].map(
                          (n) => `/images/hard-braking-${n}.png`,
                        )[selectedEvent.eventIndex % 3]
                      }
                      alt="Event Occurrence"
                      style={{ width: "100%", height: "auto" }}
                    />
                    <p>
                      <strong>Timestamp:</strong>{" "}
                      {new Date(selectedEvent.timestamp).toLocaleString()}
                    </p>
                  </Modal>
                )}
              </>
            ) : (
              <StatusIndicator type="loading">Loading...</StatusIndicator>
            )}
          </Container>
        </div>
      }
    />
  );
}
