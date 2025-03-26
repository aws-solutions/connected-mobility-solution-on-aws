// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { Breadcrumbs } from "../commons/breadcrumbs";
import { BreadcrumbGroupProps } from "@cloudscape-design/components";

export function AlertsBreadcrumbs({
  items,
}: {
  items: BreadcrumbGroupProps["items"];
}) {
  return (
    <Breadcrumbs items={[{ text: "Alerts", href: "" }, ...items]}></Breadcrumbs>
  );
}
