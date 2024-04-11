// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

export interface IPageProps {
  region: string;
  title: string;
}

export interface ISimDetailsProps {
  region: string;
  title: string;
  topicPrefix: string;
}

export interface IAttribute {
  name: string;
  type: string;
  charSet?: string;
  length?: number;
  default?: string | number;
  static?: boolean;
  tsformat?: string;
  precision?: number;
  min?: number;
  max?: number;
  lat?: number;
  long?: number;
  radius?: number;
  arr?: string[] | string;
  object?: IAttribute;
  payload?: IAttribute[];
}

export interface IDeviceType {
  name: string;
  topic: string;
  type_id: string;
  payload: Array<IAttribute>;
  created_datetime?: string;
  updated_datetime?: string;
}

export interface IDevice {
  type_id: string;
  name: string;
  amount: number;
}

export interface ISimulation {
  sim_id: string;
  name: string;
  stage: string;
  duration: number;
  interval: number;
  devices: Array<IDevice>;
  runs?: number;
  last_run?: string;
  created_datetime?: string;
  updated_datetime?: string;
  checked?: boolean;
}

export type IErrors<T> = {
  [key in keyof T]?: string;
};

export const AttributeTypeMap = {
  default: ["string", "number"],
  name: "string",
  type: "string",
  charSet: "string",
  length: "number",
  static: "boolean",
  tsformat: "string",
  precision: "number",
  min: "number",
  max: "number",
  lat: "number",
  long: "number",
  radius: "number",
  arr: "object",
  object: "object",
  payload: "object",
};

export enum simTypes {
  autoDemo = "idsAutoDemo",
  custom = "custom",
}
