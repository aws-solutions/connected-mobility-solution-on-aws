// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { renderWithEffects } from "@backstage/test-utils";
import App from "../App";

beforeAll(() => {
  window.open = jest.fn();
});

describe("App", () => {
  it("should render", async () => {
    process.env = {
      NODE_ENV: "test",
      APP_CONFIG: [
        {
          data: {
            app: { title: "Test" },
            auth: {
              environment: "production",
            },
            backend: { baseUrl: "http://localhost:7007" },
            techdocs: {
              storageUrl: "http://localhost:7007/api/techdocs/static/docs",
            },
          },
          context: "test",
        },
      ] as any,
    };

    const rendered = await renderWithEffects(<App />);
    expect(rendered.baseElement).toBeInTheDocument();
  });
});
