// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { Page, Header, Content } from '@backstage/core-components';
import {
  ClockConfig,
  HeaderWorldClock,
  HomePageStarredEntities,
} from '@backstage/plugin-home';
import { HomePageSearchBar } from '@backstage/plugin-search';
import { Grid, makeStyles } from '@material-ui/core';
import { useUserProfile } from '@backstage/plugin-user-settings';
import React from 'react';

export const HomePage = () => {
  const clockConfigs: ClockConfig[] = [
    {
      label: 'East Coast',
      timeZone: 'America/New_York',
    },
    {
      label: 'Central',
      timeZone: 'America/Chicago',
    },
    {
      label: 'Mountain',
      timeZone: 'America/Denver',
    },
    {
      label: 'Pacific',
      timeZone: 'America/Los_Angeles',
    },
  ];

  const timeFormat: Intl.DateTimeFormatOptions = {
    hour: '2-digit',
    minute: '2-digit',
    hour12: true,
  };

  const userProfile = useUserProfile();

  const useStyles = makeStyles(theme => ({
    searchBar: {
      display: 'flex',
      maxWidth: '60vw',
      backgroundColor: theme.palette.background.paper,
      boxShadow: theme.shadows[1],
      borderRadius: '50px',
      margin: 'auto',
    },
  }));

  const classes = useStyles();

  return (
    <Page themeId="home">
      <Header
        title={`Welcome, ${userProfile.displayName}`}
        pageTitleOverride="Home"
      >
        <HeaderWorldClock
          clockConfigs={clockConfigs}
          customTimeFormat={timeFormat}
        />
      </Header>
      <Content>
        <Grid container justifyContent="center">
          <Grid item xs={12} md={6}>
            <HomePageSearchBar
              classes={{ root: classes.searchBar }}
              placeholder="Search"
            />
          </Grid>
        </Grid>
        <Grid container>
          <Grid item xs={12} md={6}>
            <HomePageStarredEntities />
          </Grid>
          <Grid item xs={12} md={6}>

          </Grid>
        </Grid>
      </Content>
    </Page>
  );
};
