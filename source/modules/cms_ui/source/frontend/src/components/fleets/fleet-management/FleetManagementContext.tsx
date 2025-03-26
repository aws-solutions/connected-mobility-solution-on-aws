// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { Breadcrumbs } from "@/components/commons/breadcrumbs";
import { UI_ROUTES } from "@/utils/constants";
import { BreadcrumbGroupProps } from "@cloudscape-design/components";
import { createContext, ReactNode, useEffect, useMemo, useState } from "react";
import { Breadcrumb, BreadcrumbItemProps } from "react-bootstrap";

type BreadcrumbContextType = {
  breadcrumbItems: BreadcrumbGroupProps["items"];
  setBreadcrumbItems: (items: BreadcrumbGroupProps["items"]) => void;
};

type FleetManagementContextType = {
  breadcrumbs: BreadcrumbContextType;
};

const DEFAULT_CONTEXT: FleetManagementContextType = {
  breadcrumbs: {
    breadcrumbItems: [],
    setBreadcrumbItems: () => {},
  },
};

export const FleetManagementContext =
  createContext<FleetManagementContextType>(DEFAULT_CONTEXT);

export const FleetManagementContextProvider = ({
  children,
}: {
  children: React.ReactNode;
}) => {
  const [breadcrumbItems, setBreadcrumbItems] = useState<
    BreadcrumbGroupProps["items"]
  >([]);

  const breadcrumbs = {
    breadcrumbItems: breadcrumbItems,
    setBreadcrumbItems: setBreadcrumbItems,
  };

  const contextValue = useMemo(
    () => ({
      breadcrumbs: breadcrumbs,
    }),
    [breadcrumbs],
  );

  return (
    <FleetManagementContext.Provider value={contextValue}>
      {children}
    </FleetManagementContext.Provider>
  );
};
