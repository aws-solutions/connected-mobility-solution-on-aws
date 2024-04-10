// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { render, screen, waitFor } from "@testing-library/react";
import DeviceFields from "../DeviceFields";
import { simTypes, IDeviceType } from "../../Shared/Interfaces";
import { API } from "@aws-amplify/api";
import { I18n } from "@aws-amplify/core";

const mockDeviceTypes: IDeviceType[] = [
  {
    name: "test",
    topic: "test",
    type_id: "test",
    payload: [
      {
        name: "test",
        type: "test",
      },
    ],
  },
];

const mockAPI = {
  get: async () => mockDeviceTypes,
};
jest.mock("@aws-amplify/api");
API.get = mockAPI.get;

describe("DeviceFields", () => {
  it("should render", async () => {
    render(
      <DeviceFields
        errs={[
          {
            name: "test",
          },
        ]}
        setErrs={() => {}}
        setShowValidation={() => {}}
        setSimulation={() => {}}
        showValidation={[1]}
        simType={simTypes.custom}
        simulation={{
          devices: [
            {
              amount: 1,
              name: "test",
              type_id: "test",
            },
          ],
          interval: 1,
          duration: 10,
          name: "test",
          stage: "sleeping",
          sim_id: "test",
        }}
      />,
    );

    await waitFor(() =>
      expect(
        screen.getByText(I18n.get("device.type.select")),
      ).toBeInTheDocument(),
    );
  });
});
