// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

/*
 * Copyright 2022 The Backstage Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import { Link, MarkdownContent, UserIcon } from "@backstage/core-components";
import {
  IconComponent,
  useAnalytics,
  useApp,
} from "@backstage/core-plugin-api";
import Box from "@material-ui/core/Box";
import Card from "@material-ui/core/Card";
import CardActions from "@material-ui/core/CardActions";
import CardContent from "@material-ui/core/CardContent";
import Chip from "@material-ui/core/Chip";
import Divider from "@material-ui/core/Divider";
import Button from "@material-ui/core/Button";
import Grid from "@material-ui/core/Grid";
import { makeStyles, Theme } from "@material-ui/core/styles";
import LanguageIcon from "@material-ui/icons/Language";
import { useCallback } from "react";
import { CardHeader } from "./CardHeader";
import { CardLink } from "./CardLink";
import { PartnerOfferingEntityV1beta1 } from "backstage-plugin-acdp-common";

const useStyles = makeStyles<Theme>((theme) => ({
  box: {
    overflow: "hidden",
    textOverflow: "ellipsis",
    display: "-webkit-box",
    "-webkit-line-clamp": 10,
    "-webkit-box-orient": "vertical",
  },
  markdown: {
    /** to make the styles for React Markdown not leak into the description */
    "& :first-child": {
      margin: 0,
    },
  },
  label: {
    color: theme.palette.text.secondary,
    textTransform: "uppercase",
    fontWeight: "bold",
    letterSpacing: 0.5,
    lineHeight: 1,
    fontSize: "0.75rem",
  },
  footer: {
    display: "flex",
    justifyContent: "space-between",
    flex: 1,
    alignItems: "center",
  },
  ownedBy: {
    display: "flex",
    alignItems: "center",
    flex: 1,
    color: theme.palette.link,
  },
}));

/**
 * The Props for the {@link PartnerOfferingCard} component
 * @alpha
 */
export interface PartnerOfferingCardProps {
  partnerOffering: PartnerOfferingEntityV1beta1;
  additionalLinks?: {
    icon: IconComponent;
    text: string;
    url: string;
  }[];

  onSelected?: (partnerOffering: PartnerOfferingEntityV1beta1) => void;
}

/**
 * The `PartnerOfferingCard` component that is rendered in a list for each partner offering
 * @alpha
 */
export const PartnerOfferingCard = (props: PartnerOfferingCardProps) => {
  const { onSelected, partnerOffering: partnerOffering } = props;
  const styles = useStyles();
  const analytics = useAnalytics();
  const app = useApp();
  const iconResolver = (key?: string): IconComponent =>
    key ? app.getSystemIcon(key) ?? LanguageIcon : LanguageIcon;
  const hasTags = !!partnerOffering.metadata.tags?.length;
  const hasLinks =
    !!props.additionalLinks?.length || !!partnerOffering.metadata.links?.length;
  const displayDefaultDivider = !hasTags && !hasLinks;

  const handleChoose = useCallback(() => {
    analytics.captureEvent("click", `PartnerOffering has been opened`);
    onSelected?.(partnerOffering);
  }, [analytics, onSelected, partnerOffering]);

  return (
    <Card>
      <CardHeader partnerOffering={partnerOffering} />
      <CardContent>
        <Grid container spacing={2}>
          <Grid item xs={12}>
            <Box className={styles.box}>
              <MarkdownContent
                className={styles.markdown}
                content={
                  partnerOffering.metadata.description ?? "No description"
                }
              />
            </Box>
          </Grid>
          {displayDefaultDivider && (
            <Grid item xs={12}>
              <Divider data-testid="partnerOffering-card-separator" />
            </Grid>
          )}
          {hasTags && (
            <>
              <Grid item xs={12}>
                <Divider data-testid="partnerOffering-card-separator--tags" />
              </Grid>
              <Grid item xs={12}>
                <Grid container spacing={2}>
                  {partnerOffering.metadata.tags?.map((tag) => (
                    <Grid key={`grid-${tag}`} item>
                      <Chip
                        style={{ margin: 0 }}
                        size="small"
                        label={tag}
                        key={tag}
                      />
                    </Grid>
                  ))}
                </Grid>
              </Grid>
            </>
          )}
          {hasLinks && (
            <>
              <Grid item xs={12}>
                <Divider data-testid="partnerOffering-card-separator--links" />
              </Grid>
              <Grid item xs={12}>
                <Grid container spacing={2}>
                  {props.additionalLinks?.map(({ icon, text, url }, index) => (
                    <Grid
                      className={styles.linkText}
                      item
                      xs={6}
                      key={`${text}-${index}`}
                    >
                      <CardLink icon={icon} text={text} url={url} />
                    </Grid>
                  ))}
                  {partnerOffering.metadata.links?.map(
                    ({ url, icon, title }, index) => (
                      <Grid
                        className={styles.linkText}
                        item
                        xs={6}
                        key={`${title}-${index}`}
                      >
                        <CardLink
                          icon={iconResolver(icon)}
                          text={title || url}
                          url={url}
                        />
                      </Grid>
                    ),
                  )}
                </Grid>
              </Grid>
            </>
          )}
        </Grid>
      </CardContent>
      <CardActions style={{ padding: "16px", flex: 1, alignItems: "flex-end" }}>
        <div className={styles.footer}>
          <div className={styles.footer}>
            {(partnerOffering.spec.author?.length ?? 0) > 0 && (
              <>
                <UserIcon fontSize="small" />
                {(partnerOffering.spec.authorPageUrl?.length ?? 0) > 0 ? (
                  <Link
                    to={partnerOffering.spec.authorPageUrl ?? ""}
                    target="_blank"
                    className={styles.ownedBy}
                    style={{ marginLeft: "8px" }}
                  >
                    {partnerOffering.spec.author}
                  </Link>
                ) : (
                  <span className={styles.footer} style={{ marginLeft: "8px" }}>
                    {partnerOffering.spec.author}
                  </span>
                )}
              </>
            )}
          </div>
          <Button
            size="small"
            variant="outlined"
            color="primary"
            onClick={handleChoose}
          >
            Choose
          </Button>
        </div>
      </CardActions>
    </Card>
  );
};
