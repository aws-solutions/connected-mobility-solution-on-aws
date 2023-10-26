// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import express from 'express';
import request from 'supertest';
import { customErrorHandler } from './customErrorHandler';
import {
  AuthenticationError,
  ConflictError,
  InputError,
  NotAllowedError,
  NotFoundError,
  NotModifiedError,
} from '@backstage/errors';
import createError from 'http-errors';

type ErrorCause = {
  name: string
  message: string
  stack: string
}

class CustomError extends Error {
  cause: ErrorCause
  constructor(message: string, stack: string) {
    super(message);
    this.name = "CustomError"
    this.cause = {name: "CustomError", message: message, stack: stack};
    this.stack = stack;
  }
};

describe('customErrorHandler', () => {
  let app: express.Application;

  beforeEach(function () {
    app = express();
  });

  it('gives default code and message', async () => {
    app.use('/breaks', () => {
      throw new Error('some message');
    });
    app.use(customErrorHandler());

    const response = await request(app).get('/breaks');

    expect(response.status).toBe(500);
    expect(response.body).toEqual({
      error: expect.objectContaining({
        name: 'Error',
        message: 'some message',
      }),
      request: { method: 'GET', url: '/breaks' },
      response: { statusCode: 500 },
    });
  });

  it('does not try to send the response again if it has already been sent', async () => {
    const mockSend = jest.fn();

    app.use('/works_with_async_fail', (_, res) => {
      res.status(200).send('hello');

      // mutate the response object to test the middleware.
      // it's hard to catch errors inside middleware from the outside.
      res.send = mockSend;
      throw new Error('some message');
    });

    app.use(customErrorHandler());
    const response = await request(app).get('/works_with_async_fail');

    expect(response.status).toBe(200);
    expect(response.text).toBe('hello');

    expect(mockSend).not.toHaveBeenCalled();
  });

  it('takes code from http-errors library errors', async () => {
    app.use('/breaks', () => {
      throw createError(432, 'Some Message');
    });
    app.use(customErrorHandler());

    const response = await request(app).get('/breaks');

    expect(response.status).toBe(432);
    expect(response.body).toEqual({
      error: {
        expose: true,
        name: 'BadRequestError',
        message: 'Some Message',
        status: 432,
        statusCode: 432,
      },
      request: {
        method: 'GET',
        url: '/breaks',
      },
      response: { statusCode: 432 },
    });
  });

  it.each([
    ['/NotModifiedError', NotModifiedError, 304],
    ['/InputError', InputError, 400],
    ['/AuthenticationError', AuthenticationError, 401],
    ['/NotAllowedError', NotAllowedError, 403],
    ['/NotFoundError', NotFoundError, 404],
    ['/ConflictError', ConflictError, 409],
  ])('handles well-known error classes', async (path, error, statusCode) => {
    app.use(path, () => {
      throw new error();
    });
    app.use(customErrorHandler());

    const r = request(app);

    expect((await r.get(path)).status).toBe(statusCode);
    if (statusCode != 304) {
      expect((await r.get(path)).body.error.name).toBe(error.name);
    }
  });

  it('logs all 500 errors', async () => {
    const mockLogger = { child: jest.fn(), error: jest.fn() };
    mockLogger.child.mockImplementation(() => mockLogger as any);

    const thrownError = new Error('some error');

    app.use('/breaks', () => {
      throw thrownError;
    });
    app.use(customErrorHandler({ logger: mockLogger as any }));

    await request(app).get('/breaks');

    expect(mockLogger.error).toHaveBeenCalledWith(
      'Request failed with status 500',
      thrownError,
    );
  });

  it('does not log 400 errors', async () => {
    const mockLogger = { child: jest.fn(), error: jest.fn() };
    mockLogger.child.mockImplementation(() => mockLogger as any);

    app.use('/NotFound', () => {
      throw new NotFoundError();
    });
    app.use(customErrorHandler({ logger: mockLogger as any }));

    await request(app).get('/NotFound');

    expect(mockLogger.error).not.toHaveBeenCalled();
  });

  it('log 400 errors when logClientErrors is true', async () => {
    const mockLogger = { child: jest.fn(), error: jest.fn() };
    mockLogger.child.mockImplementation(() => mockLogger as any);

    app.use('/NotFound', () => {
      throw new NotFoundError();
    });
    app.use(customErrorHandler({ logger: mockLogger as any, logClientErrors: true }));

    await request(app).get('/NotFound');

    expect(mockLogger.error).toHaveBeenCalled();
  });

  it('dont show stack trace from error', async () => {
    app.use('/breaks', () => {
      throw new CustomError('some message', 'DANGEROUS STACK TRACE');
    });
    app.use(customErrorHandler({showStackTraces: false}));

    const response = await request(app).get('/breaks');

    expect(response.status).toBe(500);
    expect(response.body).toEqual({
      error: {
        name: 'CustomError',
        message: 'some message',
      },
      request: { method: 'GET', url: '/breaks' },
      response: { statusCode: 500 },
    });
  });

  it('shows stack trace from error', async () => {
    app.use('/breaks', () => {
      throw new CustomError('some message', 'DANGEROUS STACK TRACE');
    });
    app.use(customErrorHandler({showStackTraces: true}));

    const response = await request(app).get('/breaks');

    expect(response.status).toBe(500);
    expect(response.body).toEqual({
      error: {
        name: 'CustomError',
        message: 'some message',
        stack: 'DANGEROUS STACK TRACE',
        cause: {
          name: 'CustomError',
          message: 'some message',
          stack: 'DANGEROUS STACK TRACE',
        }
      },
      request: { method: 'GET', url: '/breaks' },
      response: { statusCode: 500 },
    });
  });
});
