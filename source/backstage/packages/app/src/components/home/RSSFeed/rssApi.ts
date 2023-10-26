// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { useEffect, useState } from 'react';
import {
  useApi,
  identityApiRef,
  discoveryApiRef,
} from '@backstage/core-plugin-api';

export type AtomItem = {
  title: string;
  pubDate?: string;
  published?: string;
  description: string;
  content: string;
  link: string;
};

const parseItem = (item: Element): AtomItem => {
  const itemData: { [key: string]: any } = {};
  item.childNodes.forEach(node => {
    itemData[node.nodeName] = node.textContent;
  });
  return itemData as AtomItem;
};

export const useRssFeed = (feed?: string) => {
  const [status, setStatus] = useState<{
    loading: boolean;
    error?: Error;
    data?: AtomItem[];
  }>({
    loading: false,
  });

  const identityApi = useApi(identityApiRef);
  const discoveryApi = useApi(discoveryApiRef);

  const loadFeed = async (feed: string) => {
    setStatus({ loading: true });
    const feedUrl = `${await discoveryApi.getBaseUrl('proxy')}/rss/${feed}`;
    const authToken = `Bearer ${await (
      await identityApi.getCredentials()
    ).token}`;
    const response = await fetch(feedUrl, {
      headers: {
        Authorization: authToken,
      },
    });

    if (!response.ok) {
      setStatus({
        loading: false,
        error: new Error(
          `Failed to fetch feed ${feed}: ${response.statusText}`,
        ),
      });
    } else {
      const rssTextData = await response.text();
      const rssData = new DOMParser().parseFromString(rssTextData, 'text/xml');
      const items = Array.from(rssData.querySelectorAll('item,entry')).map(
        parseItem,
      );
      setStatus({ loading: false, data: items });
    }
  };

  useEffect(() => {
    if (feed) {
      loadFeed(feed);
    }
  }, []);

  return { ...status, loadFeed };
};
