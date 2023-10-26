// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { ItemCardGrid, ItemCardHeader, Link } from '@backstage/core-components';
import { Grid, Typography } from '@material-ui/core';
import Card from '@material-ui/core/Card';
import CardActions from '@material-ui/core/CardActions';
import CardContent from '@material-ui/core/CardContent';
import CardMedia from '@material-ui/core/CardMedia';
import React from 'react';
import { useRssFeed } from './rssApi';
import { Sanitized } from './sanitized';

export interface RSSFeedProps {
  rssSource: string;
  title: string;
}

export const RSSFeed = ({ rssSource, title }: RSSFeedProps) => {
  const { data } = useRssFeed(rssSource);
  return (
    <Grid container spacing={1}>
      <Grid item xs={12}>
        <Typography variant="h6">{title}</Typography>
      </Grid>
      <Grid
        item
        xs={12}
        style={{
          maxHeight: '40vh',
          overflowY: 'auto',
          overflowX: 'hidden',
        }}
      >
        <ItemCardGrid>
          {data &&
            data.map(item => (
              <Card key={item.title}>
                <CardMedia>
                  <ItemCardHeader
                    title={item.title}
                    subtitle={item.pubDate || item.published || ''}
                  />
                </CardMedia>
                <CardContent
                  style={{
                    maxHeight: '30vh',
                    overflowY: 'hidden',
                    overflowX: 'hidden',
                  }}
                >
                  <Sanitized text={item.description || item.content} />
                </CardContent>
                <CardActions>
                  <Link to={item.link}>Go to the article...</Link>
                </CardActions>
              </Card>
            ))}
        </ItemCardGrid>
      </Grid>
    </Grid>
  );
};
