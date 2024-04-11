// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { getAttrFields, validateFileContents } from "../Utils";
import { IDeviceType, simTypes } from "../../components/Shared/Interfaces";

describe("getAttrFields", () => {
  const cases: Array<[string, string[]]> = [
    ["id", ["charSet", "length", "static"]],
    ["bool", ["default"]],
    ["int", ["min", "max", "default"]],
    ["sinusoidal", ["min", "max", "default"]],
    ["decay", ["min", "max", "default"]],
    ["float", ["min", "max", "precision", "default"]],
    ["location", ["lat", "long", "radius"]],
    ["string", ["min", "max", "static", "default"]],
    ["timestamp", ["tsformat", "default"]],
    ["pickOne", ["arr", "static"]],
    ["object", ["payload"]],
    ["", []],
  ];

  it.each(cases)(
    "should return the correct fields for type",
    (type, expected) => {
      const attrFields = getAttrFields(type);
      expect(attrFields).toStrictEqual(expected);
    },
  );
});

describe("validateFileContents", () => {
  it("it should not throw error for valid file contents", () => {
    const validDeviceType: IDeviceType = {
      name: "test",
      topic: "test",
      type_id: simTypes.custom,
      payload: [
        {
          name: "test_id",
          type: "id",
          static: false,
        },
        {
          name: "test_location",
          type: "location",
          lat: 0,
          long: 0,
          radius: 10,
          static: false,
        },
      ],
    };
    expect(() => validateFileContents(validDeviceType)).not.toThrow();
  });

  it("it should throw error for invalid file contents", () => {
    const invalidDeviceTopic: IDeviceType = {
      name: "test",
      topic: "#",
      type_id: simTypes.custom,
      payload: [
        {
          name: "test",
          type: "id",
          static: false,
        },
      ],
    };
    expect(() => validateFileContents(invalidDeviceTopic)).toThrow();
  });

  it("it should throw error for invalid file contents", () => {
    const invalidDeviceTypeId: IDeviceType = {
      name: "test",
      topic: "test",
      type_id: 1,
      payload: [
        {
          name: "test",
          type: "id",
          static: false,
        },
      ],
    };
    expect(() => validateFileContents(invalidDeviceTypeId)).toThrow();
  });

  it("it should throw error for invalid file contents", () => {
    const invalidDevicePayload: IDeviceType = {
      name: "test",
      topic: "test",
      type_id: simTypes.custom,
      payload: [{}],
    };
    expect(() => validateFileContents(invalidDevicePayload)).toThrow();
  });
});
