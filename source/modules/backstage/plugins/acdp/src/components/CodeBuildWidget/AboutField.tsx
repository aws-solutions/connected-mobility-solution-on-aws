// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React from "react";

import { Grid, makeStyles, Typography } from "@material-ui/core";

const useStyles = makeStyles((theme) => ({
  links: {
    margin: theme.spacing(2, 0),
    display: "grid",
    gridAutoFlow: "column",
    gridAutoColumns: "min-content",
    gridGap: theme.spacing(3),
  },
  label: {
    color: theme.palette.text.secondary,
    textTransform: "uppercase",
    fontSize: "10px",
    fontWeight: "bold",
    letterSpacing: 0.5,
    overflow: "hidden",
    whiteSpace: "nowrap",
  },
  value: {
    fontWeight: "bold",
    overflow: "hidden",
    lineHeight: "24px",
    wordBreak: "break-word",
  },
  description: {
    wordBreak: "break-word",
  },
}));

interface AboutFieldProps {
  label: string;
  gridSizes?: Record<string, number>;
  children?: React.ReactNode;
}

export const AboutField = (props: AboutFieldProps) => {
  const { label, gridSizes, children } = props;

  const classes = useStyles();

  return (
    <Grid item {...gridSizes}>
      <Typography
        variant="subtitle2"
        className={classes.label}
        children={label}
      />
      {children}
    </Grid>
  );
};
