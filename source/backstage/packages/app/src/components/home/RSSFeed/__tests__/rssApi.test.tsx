// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { useRssFeed } from '../rssApi';
import { screen, waitFor } from '@testing-library/react';
import { renderWithEffects } from '@backstage/test-utils';
import React from 'react';

jest.mock('@backstage/core-plugin-api', () => ({
  ...jest.requireActual('@backstage/core-plugin-api'),
  useApi: jest.fn().mockReturnValue({
    getBaseUrl: jest.fn().mockReturnValue('http://localhost:3000'),
    getCredentials: jest.fn().mockReturnValue('test-token'),
  }),
}));

beforeAll(() => {
  const mockFeedResponse = {
    ok: true,
    text: jest
      .fn()
      .mockResolvedValue(
        '<?xml version="1.0" encoding="UTF-8"?>' +
          '<root>' +
          '<item>' +
          '<title>test-1</title>' +
          '</item>' +
          '<item>' +
          '<title>test-2</title>' +
          '</item>' +
          '</root>',
      ),
  };

  global.fetch = jest.fn().mockReturnValue(mockFeedResponse);
});

describe('rssApi', () => {
  it('useRssFeed loads feed as expected', async () => {
    const MockComponentWithRssFeed = () => {
      const { data } = useRssFeed('test');
      return (
        <div>
          {data?.map((row, i) => (
            <div key={`${row}-${i}`}>{row.title}</div>
          ))}
        </div>
      );
    };
    await renderWithEffects(<MockComponentWithRssFeed />);
    await waitFor(() => {
      expect(screen.getByText('test-1')).toBeInTheDocument();
      expect(screen.getByText('test-2')).toBeInTheDocument();
    });
  });
});
