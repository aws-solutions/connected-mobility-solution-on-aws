// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { handler } from "../index"; // adjust the import path as needed
import { FleetManagement } from "../service";
import * as apiServerModule from "@com.cms.fleetmanagement/api-server";
import * as utils from "../utils";
import { APIGatewayProxyEvent, Context } from "aws-lambda";

// Mock the modules
jest.mock("../service");
jest.mock("@com.cms.fleetmanagement/api-server");
jest.mock("../utils");

describe("Lambda Handler Tests", () => {
  // Setup common test variables
  let mockEvent: APIGatewayProxyEvent;
  let mockContext: Context;
  let mockHttpRequest: any;
  let mockHttpResponse: any;
  let mockServiceHandler: any;

  beforeEach(() => {
    // Reset all mocks before each test
    jest.clearAllMocks();

    // Mock console.error
    jest.spyOn(console, "error").mockImplementation(() => {});

    // Setup mock data
    mockEvent = {
      body: JSON.stringify({ action: "getFleets" }),
      headers: { "Content-Type": "application/json" },
      multiValueHeaders: {},
      httpMethod: "POST",
      isBase64Encoded: false,
      path: "/fleet",
      pathParameters: null,
      queryStringParameters: null,
      multiValueQueryStringParameters: null,
      stageVariables: null,
      requestContext: {} as any,
      resource: "",
    } as APIGatewayProxyEvent;

    mockContext = {
      callbackWaitsForEmptyEventLoop: true,
      functionName: "lambda-function",
      functionVersion: "1",
      invokedFunctionArn: "arn:aws:lambda",
      memoryLimitInMB: "128",
      awsRequestId: "123456",
      logGroupName: "log-group",
      logStreamName: "log-stream",
      getRemainingTimeInMillis: jest.fn().mockReturnValue(5000),
      done: jest.fn(),
      fail: jest.fn(),
      succeed: jest.fn(),
    } as unknown as Context;

    mockHttpRequest = {
      method: "POST",
      path: "/fleet",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: "getFleets" }),
    };

    mockHttpResponse = {
      statusCode: 200,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ fleets: [] }),
      isBase64Encoded: false,
    };

    mockServiceHandler = {
      handle: jest.fn().mockResolvedValue(mockHttpResponse),
    };

    // Setup mocks for imported functions
    (utils.convertApiGatewayEventToHttpRequest as jest.Mock).mockReturnValue(
      mockHttpRequest,
    );
    (
      utils.convertHttpResponseToApiGatewayResponse as jest.Mock
    ).mockResolvedValue({
      statusCode: 200,
      body: JSON.stringify({ fleets: [] }),
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
      },
      isBase64Encoded: false,
    });
    (
      apiServerModule.getFleetManagementServiceHandler as jest.Mock
    ).mockReturnValue(mockServiceHandler);
  });

  test("should successfully process a valid request", async () => {
    // Execute the handler
    const result = await handler(mockEvent, mockContext);

    // Verify the FleetManagement service was instantiated
    expect(FleetManagement).toHaveBeenCalledTimes(1);

    // Verify event was converted to HTTP request
    expect(utils.convertApiGatewayEventToHttpRequest).toHaveBeenCalledWith(
      mockEvent,
    );

    // Verify the service handler was called with correct parameters
    expect(
      apiServerModule.getFleetManagementServiceHandler,
    ).toHaveBeenCalledTimes(1);
    expect(mockServiceHandler.handle).toHaveBeenCalledWith(
      mockHttpRequest,
      mockContext,
    );

    // Verify HTTP response was converted to API Gateway response
    expect(utils.convertHttpResponseToApiGatewayResponse).toHaveBeenCalledWith(
      mockHttpResponse,
    );

    // Verify the final result
    expect(result).toEqual({
      statusCode: 200,
      body: JSON.stringify({ fleets: [] }),
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
      },
      isBase64Encoded: false,
    });
  });

  test("should return a 500 error when an exception occurs", async () => {
    // Setup error scenario
    const errorMessage = "Service unavailable";
    (mockServiceHandler.handle as jest.Mock).mockRejectedValue(
      new Error(errorMessage),
    );

    // Execute the handler
    const result = await handler(mockEvent, mockContext);

    // Verify the service was instantiated
    expect(FleetManagement).toHaveBeenCalledTimes(1);

    // Verify the error response
    expect(result).toEqual({
      statusCode: 500,
      body: JSON.stringify({ message: "Internal server error" }),
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
      },
      isBase64Encoded: false,
    });

    // Verify the error was logged
    expect(console.error).toHaveBeenCalledWith(
      "Error processing request:",
      expect.any(Error),
    );
  });

  test("should correctly pass context to service handler", async () => {
    // Execute the handler
    await handler(mockEvent, mockContext);

    // Verify context was correctly passed to the service handler
    expect(mockServiceHandler.handle).toHaveBeenCalledWith(
      expect.anything(),
      expect.objectContaining({
        awsRequestId: "123456",
        functionName: "lambda-function",
      }),
    );
  });

  test("should handle different HTTP methods", async () => {
    // Setup GET request
    const getEvent = {
      ...mockEvent,
      httpMethod: "GET",
      queryStringParameters: { fleetId: "123" },
    };

    const getHttpRequest = {
      ...mockHttpRequest,
      method: "GET",
      path: "/fleet",
      query: { fleetId: "123" },
    };

    (utils.convertApiGatewayEventToHttpRequest as jest.Mock).mockReturnValue(
      getHttpRequest,
    );

    // Execute the handler
    await handler(getEvent, mockContext);

    // Verify correct conversion and handling
    expect(utils.convertApiGatewayEventToHttpRequest).toHaveBeenCalledWith(
      getEvent,
    );
    expect(mockServiceHandler.handle).toHaveBeenCalledWith(
      getHttpRequest,
      mockContext,
    );
  });

  test("should correctly convert and handle binary responses", async () => {
    // Setup binary response
    const binaryResponse = {
      statusCode: 200,
      headers: { "Content-Type": "application/pdf" },
      body: Buffer.from("PDF content").toString("base64"),
      isBase64Encoded: true,
    };

    (mockServiceHandler.handle as jest.Mock).mockResolvedValue(binaryResponse);

    const binaryApiGatewayResponse = {
      statusCode: 200,
      headers: {
        "Content-Type": "application/pdf",
        "Access-Control-Allow-Origin": "*",
      },
      body: Buffer.from("PDF content").toString("base64"),
      isBase64Encoded: true,
    };

    (
      utils.convertHttpResponseToApiGatewayResponse as jest.Mock
    ).mockResolvedValue(binaryApiGatewayResponse);

    // Execute the handler
    const result = await handler(mockEvent, mockContext);

    // Verify binary response was correctly processed
    expect(utils.convertHttpResponseToApiGatewayResponse).toHaveBeenCalledWith(
      binaryResponse,
    );
    expect(result).toEqual(binaryApiGatewayResponse);
  });
});
