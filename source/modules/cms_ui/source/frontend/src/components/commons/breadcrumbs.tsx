// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React from "react";
import BreadcrumbGroup, {
  BreadcrumbGroupProps,
} from "@cloudscape-design/components/breadcrumb-group";
import { UI_ROUTES } from "@/utils/constants";
import { useNavigate } from "react-router-dom";

export function Breadcrumbs({
  items,
}: {
  items: BreadcrumbGroupProps["items"];
}) {
  const navigate = useNavigate();

  return (
    <BreadcrumbGroup
      items={[
        { text: "Connected Mobility Solution", href: UI_ROUTES.ROOT },
        ...items,
      ]}
      expandAriaLabel="Show path"
      ariaLabel="Breadcrumbs"
      onFollow={(event) => {
        event.preventDefault();
        navigate(event.detail.href);
      }}
    />
  );
}
