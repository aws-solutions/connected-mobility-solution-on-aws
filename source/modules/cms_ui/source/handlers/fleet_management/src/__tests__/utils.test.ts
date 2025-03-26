// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { APIGatewayProxyEvent } from "aws-lambda";
import { HttpRequest } from "@smithy/protocol-http";
import {
  convertApiGatewayEventToHttpRequest,
  convertHttpResponseToApiGatewayResponse,
} from "../utils"; // adjust import path as needed

describe("API Gateway Conversion Utilities", () => {
  describe("convertApiGatewayEventToHttpRequest", () => {
    test("should convert a simple API Gateway event to an HTTP request", () => {
      // Arrange
      const event: APIGatewayProxyEvent = {
        httpMethod: "GET",
        path: "/users",
        headers: {
          "Content-Type": "application/json",
          Authorization: "Bearer token123",
        },
        queryStringParameters: { page: "1", limit: "10" },
        pathParameters: null,
        stageVariables: null,
        requestContext: {
          accountId: "123456789012",
          apiId: "api-id",
          domainName: "api.example.com",
          domainPrefix: "api",
          extendedRequestId: "request-id",
          httpMethod: "GET",
          authorizer: {},
          identity: {
            accessKey: null,
            accountId: null,
            apiKey: null,
            apiKeyId: null,
            caller: null,
            cognitoAuthenticationProvider: null,
            cognitoAuthenticationType: null,
            cognitoIdentityId: null,
            cognitoIdentityPoolId: null,
            principalOrgId: null,
            sourceIp: "127.0.0.1",
            user: null,
            userAgent: "Custom User Agent String",
            userArn: null,
            clientCert: null,
          },
          path: "/users",
          protocol: "HTTP/1.1",
          requestId: "id",
          requestTime: "04/Mar/2020:19:15:17 +0000",
          requestTimeEpoch: 1583349317135,
          resourceId: null,
          resourcePath: "/users",
          stage: "prod",
        },
        body: null,
        isBase64Encoded: false,
        multiValueHeaders: {},
        multiValueQueryStringParameters: null,
        resource: "/users",
      };

      // Act
      const result = convertApiGatewayEventToHttpRequest(event);

      // Assert
      expect(result).toBeInstanceOf(HttpRequest);
      expect(result.method).toBe("GET");
      expect(result.hostname).toBe("api.example.com");
      expect(result.path).toBe("/users");
      expect(result.query).toEqual({ page: "1", limit: "10" });
      expect(result.headers).toEqual({
        "content-type": "application/json",
        authorization: "Bearer token123",
      });
      expect(result.body).toBeUndefined();
    });

    test("should convert an API Gateway event with a JSON body", () => {
      // Arrange
      const jsonBody = JSON.stringify({
        name: "John Doe",
        email: "john@example.com",
      });
      const event: APIGatewayProxyEvent = {
        httpMethod: "POST",
        path: "/users",
        headers: {
          "Content-Type": "application/json",
        },
        queryStringParameters: null,
        pathParameters: null,
        stageVariables: null,
        requestContext: {
          accountId: "123456789012",
          apiId: "api-id",
          domainName: "api.example.com",
          domainPrefix: "api",
          extendedRequestId: "request-id",
          httpMethod: "POST",
          authorizer: {},
          identity: {
            accessKey: null,
            accountId: null,
            apiKey: null,
            apiKeyId: null,
            caller: null,
            cognitoAuthenticationProvider: null,
            cognitoAuthenticationType: null,
            cognitoIdentityId: null,
            cognitoIdentityPoolId: null,
            principalOrgId: null,
            sourceIp: "127.0.0.1",
            user: null,
            userAgent: "Custom User Agent String",
            userArn: null,
            clientCert: null,
          },
          path: "/users",
          protocol: "HTTP/1.1",
          requestId: "id",
          requestTime: "04/Mar/2020:19:15:17 +0000",
          requestTimeEpoch: 1583349317135,
          resourceId: null,
          resourcePath: "/users",
          stage: "prod",
        },
        body: jsonBody,
        isBase64Encoded: false,
        multiValueHeaders: {},
        multiValueQueryStringParameters: null,
        resource: "/users",
      };

      // Act
      const result = convertApiGatewayEventToHttpRequest(event);

      // Assert
      expect(result).toBeInstanceOf(HttpRequest);
      expect(result.method).toBe("POST");
      expect(result.path).toBe("/users");

      // Verify the body is properly converted to a Buffer with UTF-8 encoding
      const bodyBuffer = result.body as Buffer;
      expect(bodyBuffer).toBeInstanceOf(Buffer);
      expect(bodyBuffer.toString("utf8")).toBe(jsonBody);
    });

    test("should convert an API Gateway event with a base64 encoded body", () => {
      // Arrange
      const originalString = "Binary content";
      const base64Body = Buffer.from(originalString).toString("base64");
      const event: APIGatewayProxyEvent = {
        httpMethod: "POST",
        path: "/files",
        headers: {
          "Content-Type": "application/octet-stream",
        },
        queryStringParameters: null,
        pathParameters: null,
        stageVariables: null,
        requestContext: {
          accountId: "123456789012",
          apiId: "api-id",
          domainName: "api.example.com",
          domainPrefix: "api",
          extendedRequestId: "request-id",
          httpMethod: "POST",
          authorizer: {},
          identity: {
            accessKey: null,
            accountId: null,
            apiKey: null,
            apiKeyId: null,
            caller: null,
            cognitoAuthenticationProvider: null,
            cognitoAuthenticationType: null,
            cognitoIdentityId: null,
            cognitoIdentityPoolId: null,
            principalOrgId: null,
            sourceIp: "127.0.0.1",
            user: null,
            userAgent: "Custom User Agent String",
            userArn: null,
            clientCert: null,
          },
          path: "/files",
          protocol: "HTTP/1.1",
          requestId: "id",
          requestTime: "04/Mar/2020:19:15:17 +0000",
          requestTimeEpoch: 1583349317135,
          resourceId: null,
          resourcePath: "/files",
          stage: "prod",
        },
        body: base64Body,
        isBase64Encoded: true,
        multiValueHeaders: {},
        multiValueQueryStringParameters: null,
        resource: "/files",
      };

      // Act
      const result = convertApiGatewayEventToHttpRequest(event);

      // Assert
      expect(result).toBeInstanceOf(HttpRequest);
      expect(result.method).toBe("POST");

      // Verify the body is properly decoded from base64
      const bodyBuffer = result.body as Buffer;
      expect(bodyBuffer).toBeInstanceOf(Buffer);
      expect(bodyBuffer.toString("utf8")).toBe(originalString);
    });

    test("should handle missing headers in API Gateway event", () => {
      // Arrange
      const event: APIGatewayProxyEvent = {
        httpMethod: "GET",
        path: "/health",
        headers: {
          "x-custom-header": null, // Null header value
        },
        queryStringParameters: null,
        pathParameters: null,
        stageVariables: null,
        requestContext: {
          accountId: "123456789012",
          apiId: "api-id",
          domainName: null,
          domainPrefix: "api",
          extendedRequestId: "request-id",
          httpMethod: "GET",
          authorizer: {},
          identity: {
            accessKey: null,
            accountId: null,
            apiKey: null,
            apiKeyId: null,
            caller: null,
            cognitoAuthenticationProvider: null,
            cognitoAuthenticationType: null,
            cognitoIdentityId: null,
            cognitoIdentityPoolId: null,
            principalOrgId: null,
            sourceIp: "127.0.0.1",
            user: null,
            userAgent: "Custom User Agent String",
            userArn: null,
            clientCert: null,
          },
          path: "/health",
          protocol: "HTTP/1.1",
          requestId: "id",
          requestTime: "04/Mar/2020:19:15:17 +0000",
          requestTimeEpoch: 1583349317135,
          resourceId: null,
          resourcePath: "/health",
          stage: "prod",
        },
        body: null,
        isBase64Encoded: false,
        multiValueHeaders: {},
        multiValueQueryStringParameters: null,
        resource: "/health",
      };

      // Act
      const result = convertApiGatewayEventToHttpRequest(event);

      // Assert
      expect(result).toBeInstanceOf(HttpRequest);
      expect(result.method).toBe("GET");
      expect(result.hostname).toBe("localhost"); // Default hostname
      expect(result.headers).toEqual({});
    });

    test("should handle null domain name in API Gateway event", () => {
      // Arrange
      const event: APIGatewayProxyEvent = {
        httpMethod: "GET",
        path: "/health",
        headers: {},
        queryStringParameters: null,
        pathParameters: null,
        stageVariables: null,
        requestContext: {
          accountId: "123456789012",
          apiId: "api-id",
          domainName: null, // Explicitly null
          domainPrefix: "api",
          extendedRequestId: "request-id",
          httpMethod: "GET",
          authorizer: {},
          identity: {
            accessKey: null,
            accountId: null,
            apiKey: null,
            apiKeyId: null,
            caller: null,
            cognitoAuthenticationProvider: null,
            cognitoAuthenticationType: null,
            cognitoIdentityId: null,
            cognitoIdentityPoolId: null,
            principalOrgId: null,
            sourceIp: "127.0.0.1",
            user: null,
            userAgent: "Custom User Agent String",
            userArn: null,
            clientCert: null,
          },
          path: "/health",
          protocol: "HTTP/1.1",
          requestId: "id",
          requestTime: "04/Mar/2020:19:15:17 +0000",
          requestTimeEpoch: 1583349317135,
          resourceId: null,
          resourcePath: "/health",
          stage: "prod",
        },
        body: null,
        isBase64Encoded: false,
        multiValueHeaders: {},
        multiValueQueryStringParameters: null,
        resource: "/health",
      };

      // Act
      const result = convertApiGatewayEventToHttpRequest(event);

      // Assert
      expect(result).toBeInstanceOf(HttpRequest);
      expect(result.hostname).toBe("localhost"); // Default hostname
    });

    test("should handle null header values in API Gateway event", () => {
      // Arrange
      const event: APIGatewayProxyEvent = {
        httpMethod: "GET",
        path: "/users",
        headers: {
          "Content-Type": "application/json",
          "x-custom-header": null, // Null header value
        },
        queryStringParameters: null,
        pathParameters: null,
        stageVariables: null,
        requestContext: {
          accountId: "123456789012",
          apiId: "api-id",
          domainName: "api.example.com",
          domainPrefix: "api",
          extendedRequestId: "request-id",
          httpMethod: "GET",
          authorizer: {},
          identity: {
            accessKey: null,
            accountId: null,
            apiKey: null,
            apiKeyId: null,
            caller: null,
            cognitoAuthenticationProvider: null,
            cognitoAuthenticationType: null,
            cognitoIdentityId: null,
            cognitoIdentityPoolId: null,
            principalOrgId: null,
            sourceIp: "127.0.0.1",
            user: null,
            userAgent: "Custom User Agent String",
            userArn: null,
            clientCert: null,
          },
          path: "/users",
          protocol: "HTTP/1.1",
          requestId: "id",
          requestTime: "04/Mar/2020:19:15:17 +0000",
          requestTimeEpoch: 1583349317135,
          resourceId: null,
          resourcePath: "/users",
          stage: "prod",
        },
        body: null,
        isBase64Encoded: false,
        multiValueHeaders: {},
        multiValueQueryStringParameters: null,
        resource: "/users",
      };

      // Act
      const result = convertApiGatewayEventToHttpRequest(event);

      // Assert
      expect(result.headers).toEqual({
        "content-type": "application/json",
      });
      // The null header should be filtered out
      expect(result.headers).not.toHaveProperty("x-custom-header");
    });
  });

  describe("convertHttpResponseToApiGatewayResponse", () => {
    test("should convert a basic HTTP response to an API Gateway response", async () => {
      // Arrange
      const httpResponse = {
        statusCode: 200,
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: "Success" }),
      };

      // Act
      const result =
        await convertHttpResponseToApiGatewayResponse(httpResponse);

      // Assert
      expect(result).toEqual({
        statusCode: 200,
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Headers": "access-control-allow-origin",
        },
        body: JSON.stringify({ message: "Success" }),
        isBase64Encoded: false,
      });
    });

    test("should add CORS headers to API Gateway response", async () => {
      // Arrange
      const httpResponse = {
        statusCode: 204,
        headers: {},
        body: "",
      };

      // Act
      const result =
        await convertHttpResponseToApiGatewayResponse(httpResponse);

      // Assert
      expect(result.headers).toEqual({
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "access-control-allow-origin",
      });
    });

    test("should preserve existing headers in HTTP response", async () => {
      // Arrange
      const httpResponse = {
        statusCode: 200,
        headers: {
          "Content-Type": "application/json",
          "Cache-Control": "no-cache",
          "X-Custom-Header": "custom-value",
        },
        body: JSON.stringify({ data: "test" }),
      };

      // Act
      const result =
        await convertHttpResponseToApiGatewayResponse(httpResponse);

      // Assert
      expect(result.headers).toEqual({
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
        "X-Custom-Header": "custom-value",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "access-control-allow-origin",
      });
    });

    test("should handle empty body in HTTP response", async () => {
      // Arrange
      const httpResponse = {
        statusCode: 204,
        headers: {
          "Content-Type": "text/plain",
        },
        body: "",
      };

      // Act
      const result =
        await convertHttpResponseToApiGatewayResponse(httpResponse);

      // Assert
      expect(result.body).toBe("");
    });

    test("should handle null body in HTTP response", async () => {
      // Arrange
      const httpResponse = {
        statusCode: 204,
        headers: {
          "Content-Type": "text/plain",
        },
        body: null,
      };

      // Act
      const result =
        await convertHttpResponseToApiGatewayResponse(httpResponse);

      // Assert
      expect(result.body).toBeNull();
    });

    test("should handle HTTP response with different status codes", async () => {
      // Test with various status codes
      const statusCodes = [200, 201, 400, 401, 403, 404, 500];

      for (const statusCode of statusCodes) {
        // Arrange
        const httpResponse = {
          statusCode,
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ status: statusCode }),
        };

        // Act
        const result =
          await convertHttpResponseToApiGatewayResponse(httpResponse);

        // Assert
        expect(result.statusCode).toBe(statusCode);
      }
    });

    test("should maintain isBase64Encoded as false by default", async () => {
      // Arrange
      const httpResponse = {
        statusCode: 200,
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ data: "test" }),
      };

      // Act
      const result =
        await convertHttpResponseToApiGatewayResponse(httpResponse);

      // Assert
      expect(result.isBase64Encoded).toBe(false);
    });
  });
});
