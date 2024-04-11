// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { I18n, Amplify } from "@aws-amplify/core";
import { withAuthenticator, useAuthenticator } from "@aws-amplify/ui-react";
import { Geo } from "@aws-amplify/geo";
import { Auth } from "@aws-amplify/auth";
import { useEffect } from "react";
import { BrowserRouter, Route, Routes, Navigate } from "react-router-dom";
import Simulations from "./views/Simulations";
import DeviceTypeCreate from "./views/DeviceTypeCreate";
import DeviceTypes from "./views/DeviceTypes";
import Header from "./components/Shared/Header";
import PageNotFound from "./views/PageNotFound";
import SimulationCreate from "./views/SimulationCreate";
import SimulationDetails from "./views/SimulationDetails";
import { PubSub, AWSIoTProvider } from "@aws-amplify/pubsub";
import AWS from "aws-sdk";

import "@aws-amplify/ui-react/styles.css";

// Amplify configuration
declare let config: any;

// This adds a custom_header function to the config.
// The Authorization header is set for every request to the API endpoint
config.API.endpoints[0].custom_header = async () => {
  return {
    Authorization: `Bearer ${(await Auth.currentSession())
      .getIdToken()
      .getJwtToken()}`,
  };
};

Amplify.addPluggable(
  new AWSIoTProvider({
    aws_pubsub_region: config.aws_project_region,
    aws_pubsub_endpoint: "wss://" + config.aws_iot_endpoint + "/mqtt",
  }),
);
PubSub.configure(config);
Amplify.configure(config);
Geo.configure(config);

/**
 * The default application
 * @returns Amplify Authenticator with Main and Footer
 */
function App(): React.JSX.Element {
  const { authStatus } = useAuthenticator((context) => [context.authStatus]);

  useEffect(() => {
    if (authStatus == "authenticated") {
      Auth.currentCredentials().then((credentials) => {
        const identityId = credentials.identityId;
        AWS.config.update({
          region: config.aws_project_region,
          credentials: Auth.essentialCredentials(credentials),
        });
        const params = {
          policyName: config.aws_iot_policy_name,
          target: identityId,
        };

        try {
          new AWS.Iot()
            .attachPolicy(params)
            .promise()
            .then((response) => {
              console.log("Policy Attached");
            });
        } catch (error) {
          console.error(
            "Error occurred while attaching principal policy",
            error,
          );
        }
      });
    }
  }, [authStatus]);

  return (
    <div className="app-wrap">
      <Header />
      <BrowserRouter>
        <Routes>
          <Route
            path="/"
            element={<Navigate to="/simulations" replace={true} />}
          />
          <Route
            path="/simulations"
            element={
              <Simulations
                region={config.region}
                title={I18n.get("simulations")}
              />
            }
          />
          <Route
            path="/simulations/create"
            element={
              <SimulationCreate
                region={config.region}
                title={I18n.get("simulation.creation")}
              ></SimulationCreate>
            }
          />
          <Route
            path="/simulations/:sim_id"
            element={
              <SimulationDetails
                region={config.region}
                title={I18n.get("simulation.details")}
                topicPrefix={config.topic_prefix}
              />
            }
          />
          <Route
            path="/device/type"
            element={
              <DeviceTypes
                region={config.region}
                title={I18n.get("device.types")}
              />
            }
          />
          <Route
            path="/device/type/:time_id?"
            element={
              <DeviceTypeCreate
                region={config.region}
                title={I18n.get("device.type.creation")}
              />
            }
          />
          <Route path="*" element={<PageNotFound />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default withAuthenticator(App);
