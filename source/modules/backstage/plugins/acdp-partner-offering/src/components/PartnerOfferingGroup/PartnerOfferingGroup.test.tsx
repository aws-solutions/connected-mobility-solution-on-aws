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
jest.mock("../PartnerOfferingCard", () => ({
  PartnerOfferingCard: jest.fn(() => null),
}));

import { PartnerOfferingGroup } from "./PartnerOfferingGroup";
import { render } from "@testing-library/react";
import { PartnerOfferingCard } from "../PartnerOfferingCard";
import { PartnerOfferingEntityV1beta1 } from "backstage-plugin-acdp-common";

describe("PartnerOfferingGroup", () => {
  it("should render a card for each partner offering with the partner offering being passed as a prop", () => {
    const mockOnSelected = jest.fn();
    const mockPartnerOfferings: {
      partnerOffering: PartnerOfferingEntityV1beta1;
    }[] = [
      {
        partnerOffering: {
          apiVersion: "aws.amazon.com/v1beta1",
          kind: "PartnerOffering",
          metadata: { name: "test" },
          spec: {
            type: "website",
          },
        },
      },
      {
        partnerOffering: {
          apiVersion: "aws.amazon.com/v1beta1",
          kind: "PartnerOffering",
          metadata: { name: "test2" },
          spec: {
            type: "service",
          },
        },
      },
    ];

    render(
      <PartnerOfferingGroup
        onSelected={mockOnSelected}
        title="Test"
        partnerOfferings={mockPartnerOfferings}
      />,
    );

    expect(PartnerOfferingCard).toHaveBeenCalledTimes(2);

    for (const { partnerOffering } of mockPartnerOfferings) {
      expect(PartnerOfferingCard).toHaveBeenCalledWith(
        expect.objectContaining({
          partnerOffering,
          onSelected: mockOnSelected,
        }),
        {},
      );
    }
  });

  it("should use the passed in PartnerOfferingCard prop to render the partner offering card", () => {
    const mockPartnerOfferingCardComponent = jest.fn(() => null);
    const mockOnSelected = jest.fn();
    const mockPartnerOfferings: {
      partnerOffering: PartnerOfferingEntityV1beta1;
    }[] = [
      {
        partnerOffering: {
          apiVersion: "aws.amazon.com/v1beta1",
          kind: "PartnerOffering",
          metadata: { name: "test" },
          spec: {
            type: "website",
          },
        },
      },
      {
        partnerOffering: {
          apiVersion: "aws.amazon.com/v1beta1",
          kind: "PartnerOffering",
          metadata: { name: "test2" },
          spec: {
            type: "service",
          },
        },
      },
    ];

    render(
      <PartnerOfferingGroup
        onSelected={mockOnSelected}
        title="Test"
        partnerOfferings={mockPartnerOfferings}
        components={{ CardComponent: mockPartnerOfferingCardComponent }}
      />,
    );

    expect(mockPartnerOfferingCardComponent).toHaveBeenCalledTimes(2);

    for (const { partnerOffering } of mockPartnerOfferings) {
      expect(mockPartnerOfferingCardComponent).toHaveBeenCalledWith(
        expect.objectContaining({
          onSelected: mockOnSelected,
          partnerOffering,
        }),
        {},
      );
    }
  });
  it("should render the title when there are partnerOfferings in the list", () => {
    const mockPartnerOfferings: {
      partnerOffering: PartnerOfferingEntityV1beta1;
    }[] = [
      {
        partnerOffering: {
          apiVersion: "aws.amazon.com/v1beta1",
          kind: "PartnerOffering",
          metadata: { name: "test" },
          spec: { type: "website" },
        },
      },
    ];

    const { getByText } = render(
      <PartnerOfferingGroup
        onSelected={jest.fn()}
        title="Test"
        partnerOfferings={mockPartnerOfferings}
      />,
    );

    expect(getByText("Test")).toBeInTheDocument();
  });

  it("should allow for passing through a user given title component", () => {
    const TitleComponent = <p>Im a custom header</p>;
    const mockPartnerOfferings: {
      partnerOffering: PartnerOfferingEntityV1beta1;
    }[] = [
      {
        partnerOffering: {
          apiVersion: "aws.amazon.com/v1beta1",
          kind: "PartnerOffering",
          metadata: { name: "test" },
          spec: { type: "website" },
        },
      },
    ];
    const { getByText } = render(
      <PartnerOfferingGroup
        onSelected={jest.fn()}
        partnerOfferings={mockPartnerOfferings}
        title={TitleComponent}
      />,
    );

    expect(getByText("Im a custom header")).toBeInTheDocument();
  });
});
