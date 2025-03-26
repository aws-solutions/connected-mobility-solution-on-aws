// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {
  APIGatewayProxyEvent,
  APIGatewayProxyResult,
  Context,
} from "aws-lambda";
import { getFleetManagementServiceHandler } from "@com.cms.fleetmanagement/api-server";
import {
  convertApiGatewayEventToHttpRequest,
  convertHttpResponseToApiGatewayResponse,
} from "./utils";
import { FleetManagement } from "./service";

export async function handler(
  event: APIGatewayProxyEvent,
  context: Context,
): Promise<APIGatewayProxyResult> {
  try {
    const service = new FleetManagement();
    const serviceHandler = getFleetManagementServiceHandler(service);

    const httpRequest = convertApiGatewayEventToHttpRequest(event);
    const httpResponse = await serviceHandler.handle(httpRequest, context);

    return await convertHttpResponseToApiGatewayResponse(httpResponse);
  } catch (error) {
    console.error("Error processing request:", error);
    return {
      statusCode: 500,
      body: JSON.stringify({ message: "Internal server error" }),
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
      },
      isBase64Encoded: false,
    };
  }
}
