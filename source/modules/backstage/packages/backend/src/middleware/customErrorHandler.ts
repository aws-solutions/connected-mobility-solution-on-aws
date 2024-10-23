// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { Request, Response, ErrorRequestHandler, NextFunction } from "express";
import {
  MiddlewareFactoryOptions,
  MiddlewareFactoryErrorOptions,
} from "@backstage/backend-defaults/rootHttpRouter";
import {
  AuthenticationError,
  ConflictError,
  ErrorResponseBody,
  InputError,
  NotAllowedError,
  NotFoundError,
  NotModifiedError,
  ServiceUnavailableError,
  NotImplementedError,
  serializeError,
} from "@backstage/errors";

// A copy of the Backstage error Middleware which also strips the "cause" from the response
// See original: https://github.com/backstage/backstage/blob/a9455ca766ff6cdf4639621ffe123e3e614d61d1/packages/backend-defaults/src/entrypoints/rootHttpRouter/http/MiddlewareFactory.ts#L206
export function customErrorHandler(
  options: MiddlewareFactoryOptions,
  errorOptions: MiddlewareFactoryErrorOptions,
): ErrorRequestHandler {
  const showStackTraces =
    errorOptions.showStackTraces ?? process.env.NODE_ENV === "development";

  const logger = options.logger.child({
    type: "errorHandler",
  });

  return (error: Error, req: Request, res: Response, next: NextFunction) => {
    const statusCode = getStatusCode(error);
    if (errorOptions.logAllErrors || statusCode >= 500) {
      logger.error(`Request failed with status ${statusCode}`, error);
    }

    if (res.headersSent) {
      // If the headers have already been sent, do not send the response again
      // as this will throw an error in the backend.
      next(error);
      return;
    }

    // Custom addition. Remove stack and cause from error response to avoid exposing stack trace on some errors
    if (!showStackTraces) {
      delete error.stack;
      delete error.cause;
    }

    const body: ErrorResponseBody = {
      error: serializeError(error, { includeStack: showStackTraces }),
      request: { method: req.method, url: req.url },
      response: { statusCode },
    };

    res.status(statusCode).json(body);
  };
}

function getStatusCode(error: Error): number {
  // Look for common http library status codes
  const knownStatusCodeFields = ["statusCode", "status"];
  for (const field of knownStatusCodeFields) {
    const statusCode = (error as any)[field];
    if (
      typeof statusCode === "number" &&
      (statusCode | 0) === statusCode && // is whole integer
      statusCode >= 100 &&
      statusCode <= 599
    ) {
      return statusCode;
    }
  }

  // Handle well-known error types
  switch (error.name) {
    case NotModifiedError.name:
      return 304;
    case InputError.name:
      return 400;
    case AuthenticationError.name:
      return 401;
    case NotAllowedError.name:
      return 403;
    case NotFoundError.name:
      return 404;
    case ConflictError.name:
      return 409;
    case NotImplementedError.name:
      return 501;
    case ServiceUnavailableError.name:
      return 503;
    default:
      return 500;
  }
}
