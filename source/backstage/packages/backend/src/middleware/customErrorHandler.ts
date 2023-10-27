// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { Request, Response, ErrorRequestHandler, NextFunction } from 'express';
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
} from '@backstage/errors';
import { getRootLogger } from '@backstage/backend-common';
import { ErrorHandlerOptions } from '@backstage/backend-common';

export function customErrorHandler(
  options: ErrorHandlerOptions = {},
): ErrorRequestHandler {
  const showStackTraces =
  options.showStackTraces ?? process.env.NODE_ENV === 'development';

  const logger = (options.logger ?? getRootLogger()).child({
    type: 'errorHandler',
  });

  return (error: Error, req: Request, res: Response, next: NextFunction) => {
    const statusCode = getStatusCode(error);
    if (options.logClientErrors || statusCode >= 500) {
      logger.error(`Request failed with status ${statusCode}`, error);
    }

    if (res.headersSent) {
      // If the headers have already been sent, do not send the response again
      // as this will throw an error in the backend.
      next(error);
      return;
    }
    const serializedError = serializeError(error, {includeStack: showStackTraces});

    if (!showStackTraces) {
      delete serializedError.stack;
      // The cause field in some of the error messages contain
      // the `reason`, `message` and `stack` corresponding to the
      // error. The `reason` and `message` are captured in the higher
      // level `message` field and hence the entire `cause` field can
      // be removed to avoid showing stack traces in the error response.
      delete serializedError.cause;
    }

    const body: ErrorResponseBody = {
      error: serializedError,
      request: { method: req.method, url: req.url },
      response: { statusCode },
    };

    res.status(statusCode).json(body);
};
}

function getStatusCode(error: Error): number {
  // Look for common http library status codes
  const knownStatusCodeFields = ['statusCode', 'status'];
  for (const field of knownStatusCodeFields) {
    const statusCode = (error as any)[field];
    if (
      typeof statusCode === 'number' &&
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
