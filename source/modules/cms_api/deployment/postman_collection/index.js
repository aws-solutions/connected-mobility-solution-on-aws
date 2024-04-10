// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

const fs = require("fs");
const { program } = require("commander");
const {
  CloudFormationClient,
  DescribeStacksCommand,
} = require("@aws-sdk/client-cloudformation");
const Converter = require("graphql-to-postman");
const gqlData = fs.readFileSync(
  "../../source/infrastructure/assets/graphql/schemas/vss_schema.graphql",
  { encoding: "UTF8" },
);

program
  .requiredOption("--stack-name <string>", "Stack name to get CfnOutputs from")
  .option(
    "--region <string>",
    "Region stack is deployed in",
    process.env.AWS_DEFAULT_REGION,
  );
program.parse(process.argv);
const options = program.opts();

function cleanGQLData(gqlData) {
  // Need to remove AWS decorators from schema
  return gqlData.replace(new RegExp("@aws_lambda"), "");
}

async function getCfnOutputs(stackName) {
  // Get the CloudFormation stack outputs for the cms-api-stack-dev stack.
  const client = new CloudFormationClient({
    region: options.region,
  });
  const response = await client.send(
    new DescribeStacksCommand({
      StackName: stackName,
    }),
  );
  const graphql_endpoint_url = response.Stacks[0].Outputs.find((o) =>
    o.OutputKey.includes("graphqlendpointurl"),
  ).OutputValue;
  return {
    graphql_endpoint_url,
  };
}

(async () => {
  console.log(`Getting CfnOutputs for stack: ${options.stackName}`);
  const cfnOutputs = await getCfnOutputs(options.stackName);

  // Convert the GraphQL schema to Postman collection
  Converter.convert(
    { type: "string", data: cleanGQLData(gqlData) },
    { depth: 10 },
    (err, conversionResult) => {
      if (!conversionResult.result) {
        console.log("Could not convert", conversionResult.reason);
      } else {
        const collectionJSON = conversionResult.output[0].data;
        // Add the graphql_endpoint_url to the collection JSON as environmental variable
        collectionJSON.variable = [
          {
            id: "url",
            type: "any",
            value: cfnOutputs.graphql_endpoint_url,
          },
        ];
        // Add the auth to the collection JSON
        collectionJSON.auth = {
          type: "bearer",
          bearer: [
            {
              key: "token",
              value: "",
              type: "string",
            },
          ],
        };
        try {
          fs.writeFileSync(
            "./cms_graphql_api_postman_collection.json",
            JSON.stringify(collectionJSON),
          );
          console.log("File written successfully");
        } catch (err) {
          console.error(err);
        }
      }
    },
  );
})();
