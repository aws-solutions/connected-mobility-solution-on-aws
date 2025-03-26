// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { APIGatewayProxyEvent, APIGatewayProxyResult } from "aws-lambda";
import { HttpRequest } from "@smithy/protocol-http";

export function convertApiGatewayEventToHttpRequest(
  event: APIGatewayProxyEvent,
): HttpRequest {
  const headers: Record<string, string> = {};
  if (event.headers) {
    Object.entries(event.headers).forEach(([key, value]) => {
      if (value) headers[key.toLowerCase()] = value;
    });
  }

  return new HttpRequest({
    method: event.httpMethod,
    hostname: event.requestContext.domainName || "localhost",
    path: event.path,
    query: event.queryStringParameters || {},
    headers: headers,
    body: event.body
      ? Buffer.from(event.body, event.isBase64Encoded ? "base64" : "utf8")
      : undefined,
  });
}

export async function convertHttpResponseToApiGatewayResponse(
  httpResponse: any,
): Promise<APIGatewayProxyResult> {
  const body = httpResponse.body;

  return {
    statusCode: httpResponse.statusCode,
    headers: {
      ...(httpResponse.headers as { [key: string]: string }),
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Headers": "access-control-allow-origin",
    },
    body: body,
    isBase64Encoded: false,
  };
}
