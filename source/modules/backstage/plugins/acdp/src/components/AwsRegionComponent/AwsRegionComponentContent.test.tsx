// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { render, screen } from "@testing-library/react";
import { AwsRegionComponentContent } from "./AwsRegionComponentContent";
import { acdpAccountDirectoryApiRef } from "../../api/AcdpAccountDirectoryApi";
import {
  TestApiProvider,
  wrapInTestApp,
  registerMswTestHooks,
} from "@backstage/test-utils";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { setupServer } from "msw/node";
import { AnyApiRef } from "@backstage/core-plugin-api/index";
import { MockAcdpAccountDirectoryApi } from "../../mocks";
import { RJSFSchema, createSchemaUtils, ValidatorType } from "@rjsf/utils";
import AJV8Validator from "@rjsf/validator-ajv8";

const schema: RJSFSchema = {
  type: "object",
  properties: {
    targetAwsAccountId: {
      type: "string",
      title: "AWS Account ID",
    },
  },
};

const validator: ValidatorType = AJV8Validator;

const mockApi = new MockAcdpAccountDirectoryApi();
const apis: [AnyApiRef, Partial<unknown>][] = [
  [acdpAccountDirectoryApiRef, mockApi],
];

const queryClient = new QueryClient();

describe("AwsRegionComponentContent", () => {
  const worker = setupServer();
  registerMswTestHooks(worker);

  it("renders and selects an AWS account", async () => {
    render(
      wrapInTestApp(
        <TestApiProvider apis={apis}>
          <QueryClientProvider client={queryClient}>
            <AwsRegionComponentContent
              rawErrors={[]}
              formData=""
              onChange={jest.fn()}
              schema={{}}
              uiSchema={{}}
              idSchema={{ $id: "test" }}
              name="awsAccount"
              registry={{
                fields: {},
                templates: {
                  ArrayFieldTemplate: () => null,
                  ArrayFieldDescriptionTemplate: () => null,
                  ArrayFieldItemTemplate: () => null,
                  ArrayFieldTitleTemplate: () => null,
                  BaseInputTemplate: () => null,
                  DescriptionFieldTemplate: () => null,
                  ErrorListTemplate: () => null,
                  FieldErrorTemplate: () => null,
                  FieldTemplate: () => null,
                  ObjectFieldTemplate: () => null,
                  TitleFieldTemplate: () => null,
                  WrapIfAdditionalTemplate: () => null,
                  FieldHelpTemplate: () => null,
                  UnsupportedFieldTemplate: () => null,
                  ButtonTemplates: {
                    SubmitButton: () => null,
                    AddButton: () => null,
                    CopyButton: () => null,
                    MoveDownButton: () => null,
                    MoveUpButton: () => null,
                    RemoveButton: () => null,
                  },
                },
                widgets: {},
                formContext: {},
                rootSchema: schema,
                schemaUtils: createSchemaUtils<string, RJSFSchema, any>(
                  validator,
                  schema,
                ),
                translateString: () => "",
              }}
              disabled={false}
              readonly={false}
              onBlur={jest.fn()}
              onFocus={jest.fn()}
            />
          </QueryClientProvider>
        </TestApiProvider>,
      ),
    );

    expect(
      screen.getByTestId("targetAwsRegionSelectComponenet"),
    ).toBeInTheDocument();
  });
});
