// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React, { useEffect, useState } from "react";
import { useQuery, UseQueryResult } from "@tanstack/react-query";
import { LinearProgress, Link } from "@material-ui/core";

import { validate, parse } from "@aws-sdk/util-arn-parser";

import { useEntity } from "@backstage/plugin-catalog-react";
import { useApi } from "@backstage/core-plugin-api";
import { ResponseErrorPanel } from "@backstage/core-components";
import { stringifyEntityRef } from "@backstage/catalog-model";

import { AcdpApplication, constants } from "backstage-plugin-acdp-common";

import { isApplicationArnAvailable } from "../../utils";
import { acdpMetricsApiRef } from "../../api";

export const MyApplicationsWidgetContent = () => {
  const api = useApi(acdpMetricsApiRef);
  const { entity } = useEntity();
  const entityRef = stringifyEntityRef(entity);

  const [isArnAnnotationProvided, setIsArnAnnotationProvided] = useState(false);
  const [isArnAnnotationChecked, setIsArnAnnotationChecked] = useState(false);

  const [application, setApplication] = useState<AcdpApplication | undefined>();
  const [applicationArn, setApplicationArn] = useState("");
  const [applicationTag, setApplicationTag] = useState("");
  const [myApplicationsLink, setMyApplicationLink] = useState("");
  const [currentMonthCost, setCurrentMonthCost] = useState("");

  // Check for Arn annotation
  useEffect(() => {
    setIsArnAnnotationProvided(isApplicationArnAvailable(entity));
    setIsArnAnnotationChecked(true);
  }, [entity]);

  // If Arn annotation is provided, use it to set Arn
  useEffect(() => {
    if (isArnAnnotationProvided)
      setApplicationArn(
        isArnAnnotationProvided
          ? entity.metadata.annotations?.[
              constants.APP_REGISTRY_APPLICATION_ARN_ANNOTATION
            ] ?? ""
          : "",
      );
  }, [isArnAnnotationProvided, entity]);

  // If Arn annotation is not provided, enable useQuery to get application from API via the entity, and set the application state
  const getApplicationByEntityQuery = useQuery({
    queryKey: ["getApplicationByEntity"],
    queryFn: async () => {
      const applicationFromEntity = await api.getApplicationByEntity({
        entityRef: entityRef,
      });

      if (!applicationFromEntity)
        throw new Error("No AppRegistry Application Found");

      setApplication(applicationFromEntity);
      return applicationFromEntity;
    },
    enabled: isArnAnnotationChecked && !isArnAnnotationProvided,
  });

  // If Arn annotation is provided and set, enable useQuery to get application from API via the arn, and set the application state
  const getApplicationByArnQuery = useQuery({
    queryKey: ["getApplicationByArn"],
    queryFn: async () => {
      const applicationFromArn = await api.getApplicationByArn(applicationArn);

      if (!applicationFromArn)
        throw new Error("No AppRegistry Application Found");

      setApplication(applicationFromArn);
      return applicationFromArn;
    },
    enabled:
      isArnAnnotationChecked &&
      isArnAnnotationProvided &&
      Boolean(applicationArn),
  });

  // If either query is finished, successful, and the application exists, set the Arn and Tag from the response
  useEffect(() => {
    if (
      (getApplicationByEntityQuery.isSuccess ||
        getApplicationByArnQuery.isSuccess) &&
      application
    ) {
      if (!application.arn || !validate(application.arn))
        throw new Error(
          `Value for Application arn was not a valid ARN: '${application.arn}'`,
        );
      else if (!application.applicationTag)
        throw new Error(
          `Value for Application tag was not found: '${application.applicationTag}'`,
        );
      setApplicationTag(
        application.applicationTag[constants.APP_REGISTRY_AWS_APPLICATION_TAG],
      );
      setApplicationArn(application.arn);
    }
  }, [
    getApplicationByEntityQuery.isSuccess,
    getApplicationByArnQuery.isSuccess,
    application,
  ]);

  // Once the Arn is set, format and set the link
  useEffect(() => {
    if (applicationArn) {
      const parsedArn = parse(applicationArn);
      const applicationId = parsedArn.resource.split("/")[2];

      const formattedLink = `https://${parsedArn.region}.console.aws.amazon.com/console/applications/${applicationId}?region=${parsedArn.region}`;
      setMyApplicationLink(formattedLink);
    } else {
      setMyApplicationLink("");
    }
  }, [applicationArn]);

  // Once the Tag is set, get the net unblended current month cost
  const getNetUnblendedCurrentMonthCostQuery = useQuery({
    queryKey: ["getNetUnblendedCurrentMonthCost"],
    queryFn: async () => {
      const currentMonthCostResponse =
        await api.getNetUnblendedCurrentMonthCost({
          entityRef: entityRef,
          awsApplicationTag: applicationTag,
        });

      if (!currentMonthCostResponse)
        throw new Error("No current month cost Found");

      setCurrentMonthCost(currentMonthCostResponse);
      return currentMonthCostResponse;
    },
    enabled: Boolean(applicationTag),
  });

  const ErrorPanelForQuery = ({
    query,
    title,
  }: {
    query: UseQueryResult;
    title: string;
  }) => {
    return (
      <>
        {query.isError && (
          <ResponseErrorPanel error={query.error as Error} title={title} />
        )}
      </>
    );
  };

  const areQueriesLoading = () =>
    (getApplicationByEntityQuery.isLoading &&
      getApplicationByArnQuery.isLoading) ||
    getNetUnblendedCurrentMonthCostQuery.isLoading;

  // Render based on the status of the API queries and their related response states
  return (
    <>
      {(areQueriesLoading() || !(myApplicationsLink && currentMonthCost)) && (
        <LinearProgress />
      )}
      <ErrorPanelForQuery
        query={getNetUnblendedCurrentMonthCostQuery}
        title="Cost Lookup Error"
      />
      {!areQueriesLoading() &&
        getNetUnblendedCurrentMonthCostQuery.isSuccess &&
        currentMonthCost && (
          <div style={{ fontWeight: "bold" }}>
            Current Month Cost:
            <br />
            <div style={{ fontSize: "1.5em" }}>
              ${Number(currentMonthCost).toFixed(2)}
            </div>
          </div>
        )}
      <br />
      <ErrorPanelForQuery
        query={getApplicationByArnQuery}
        title="Application Lookup Error"
      />
      <ErrorPanelForQuery
        query={getApplicationByEntityQuery}
        title="Application Lookup Error"
      />
      {!areQueriesLoading() &&
        (getApplicationByEntityQuery.isSuccess || isArnAnnotationProvided) &&
        myApplicationsLink && (
          <>
            For more details, click{" "}
            <Link href={myApplicationsLink} underline="always" target="_blank">
              here
            </Link>{" "}
            to navigate to the AWS Console myApplications dashboard.
          </>
        )}
    </>
  );
};
