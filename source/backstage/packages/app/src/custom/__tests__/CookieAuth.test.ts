// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { setTokenCookie } from '../CookieAuth';
import type { IdentityApi } from '@backstage/core-plugin-api';
import jwt from 'jsonwebtoken';

beforeAll(() => {
  global.fetch = jest.fn();
  jest.useFakeTimers();
});

afterEach(() => {
  jest.resetAllMocks();
});

describe('CookieAuth', () => {
  it('Should call endpoint to set token cookie', async () => {
    const mockJwt = jwt.sign({ test: 'test' }, 'test', { expiresIn: '1h' });
    const mockIdentityApi: IdentityApi = {
      getBackstageIdentity: jest.fn(),
      getCredentials: jest.fn().mockReturnValue({ token: mockJwt }),
      getProfileInfo: jest.fn(),
      signOut: jest.fn(),
    };

    await setTokenCookie('https://localhost:3000', mockIdentityApi);
    expect(mockIdentityApi.getCredentials).toBeCalledTimes(1);
    jest.runOnlyPendingTimers();
    expect(mockIdentityApi.getCredentials).toBeCalledTimes(2);
  });

  it('Should not call endpoint to set token cookie if token is null', async () => {
    const mockIdentityApi: IdentityApi = {
      getBackstageIdentity: jest.fn(),
      getCredentials: jest.fn().mockReturnValue({ token: null }),
      getProfileInfo: jest.fn(),
      signOut: jest.fn(),
    };
    await setTokenCookie('https://localhost:3000', mockIdentityApi);
    expect(mockIdentityApi.getCredentials).toBeCalled();
    expect(global.fetch).not.toBeCalled();
  });
});
