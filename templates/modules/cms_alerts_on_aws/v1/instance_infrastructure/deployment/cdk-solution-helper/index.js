/**
 *  Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 *  Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file except in compliance
 *  with the License. A copy of the License is located at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 *  or in the 'license' file accompanying this file. This file is distributed on an 'AS IS' BASIS, WITHOUT WARRANTIES
 *  OR CONDITIONS OF ANY KIND, express or implied. See the License for the specific language governing permissions
 *  and limitations under the License.
 */

// Imports
const fs = require("fs");

// Paths
const global_s3_assets = "../global-s3-assets";

function substituteLambdaAssets(template, resources) {
  // Clean-up Lambda function code dependencies
  const lambdaFunctions = Object.keys(resources).filter(function (key) {
    return resources[key].Type === "AWS::Lambda::Function";
  });
  lambdaFunctions.forEach(function (f) {
    const fn = template.Resources[f];
    let prop;
    if (fn.Properties.hasOwnProperty("Code")) {
      prop = fn.Properties.Code;
    } else if (fn.Properties.hasOwnProperty("Content")) {
      prop = fn.Properties.Content;
    }

    if (prop.hasOwnProperty("S3Bucket")) {
      // Set the S3 key reference
      let artifactHash = Object.assign(prop.S3Key);
      const assetPath = `asset${artifactHash}`;
      prop.S3Key = `%%SOLUTION_NAME%%/%%VERSION%%/${assetPath}`;

      // Set the S3 bucket reference
      prop.S3Bucket = {
        "Fn::Sub": "%%DIST_BUCKET_NAME%%-${AWS::Region}",
      };
    } else {
      console.warn(`No S3Bucket Property found for ${JSON.stringify(prop)}`);
    }
  });
}

function substituteLambdaLayerAssets(template, resources) {
  const lambdaLayers = Object.keys(resources).filter(function (key) {
    return resources[key].Type === "AWS::Lambda::LayerVersion";
  });
  lambdaLayers.forEach(function (f) {
    const fn = template.Resources[f];
    let prop;
    if (fn.Properties.hasOwnProperty("Content")) {
      prop = fn.Properties.Content;
    }

    if (prop.hasOwnProperty("S3Bucket")) {
      // Set the S3 key reference
      let artifactHash = Object.assign(prop.S3Key);
      const assetPath = `asset${artifactHash}`;
      prop.S3Key = `%%SOLUTION_NAME%%/%%VERSION%%/${assetPath}`;

      // Set the S3 bucket reference
      prop.S3Bucket = {
        "Fn::Sub": "%%DIST_BUCKET_NAME%%-${AWS::Region}",
      };
    } else {
      console.warn(`No S3Bucket Property found for ${JSON.stringify(prop)}`);
    }
  });
}

function substituteServerlessFunctionAssets(template, resources) {
  const serverlessFunctions = Object.keys(resources).filter(function (key) {
    return resources[key].Type === "AWS::Serverless::Function";
  });
  serverlessFunctions.forEach(function (f) {
    const fn = template.Resources[f];
    let prop;
    if (fn.Properties.hasOwnProperty("CodeUri")) {
      prop = fn.Properties.CodeUri;
    }

    if (prop.hasOwnProperty("Bucket")) {
      // Set the S3 key reference
      let artifactHash = Object.assign(prop.Key);
      const assetPath = `asset${artifactHash}`;
      prop.Key = `%%SOLUTION_NAME%%/%%VERSION%%/${assetPath}`;

      // Set the S3 bucket reference
      prop.Bucket = {
        "Fn::Sub": "%%DIST_BUCKET_NAME%%-${AWS::Region}",
      };
    } else {
      console.warn(`No S3Bucket Property found for ${JSON.stringify(prop)}`);
    }
  });
}

function substituteCDKBucketDeploymentAssets(template, resources) {
  const cdkBucketDeployments = Object.keys(resources).filter(function (key) {
    return resources[key].Type === "Custom::CDKBucketDeployment";
  });
  cdkBucketDeployments.forEach(function (f) {
    const fn = template.Resources[f];
    let prop = fn.Properties;

    if (prop.hasOwnProperty("SourceBucketNames")) {
      // Set the S3 key reference
      let artifactHash = Object.assign(prop.SourceObjectKeys);
      const assetPath = `asset${artifactHash}`;
      prop.SourceObjectKeys = [`%%SOLUTION_NAME%%/%%VERSION%%/${assetPath}`];

      // Set the S3 bucket reference
      prop.SourceBucketNames = [
        {
          "Fn::Sub": "%%DIST_BUCKET_NAME%%-${AWS::Region}",
        },
      ];
    } else {
      console.warn(`No S3Bucket Property found for ${JSON.stringify(prop)}`);
    }
  });
}

function substituteCodeCommitRepoAssets(template, resources) {
  const codeCommitRepos = Object.keys(resources).filter(function (key) {
    return resources[key].Type === "AWS::CodeCommit::Repository";
  });
  codeCommitRepos.forEach(function (f) {
    const fn = template.Resources[f];
    let prop;

    if (fn.Properties.hasOwnProperty("Code")) {
      prop = fn.Properties.Code;
    }

    if (prop.hasOwnProperty("S3")) {
      prop = prop.S3;
      // Set the S3 key reference
      let artifactHash = Object.assign(prop.Key);
      const assetPath = `asset${artifactHash}`;
      prop.Key = `%%SOLUTION_NAME%%/%%VERSION%%/${assetPath}`;
      // Set the S3 bucket reference
      prop.Bucket = {
        "Fn::Sub": "%%DIST_BUCKET_NAME%%-${AWS::Region}",
      };
    } else {
      console.warn(`No S3Bucket Property found for ${JSON.stringify(prop)}`);
    }
  });
}

function substituteNestedStackAssets(template, resources) {
  // Clean-up nested template stack dependencies
  const nestedStacks = Object.keys(resources).filter(function (key) {
    return resources[key].Type === "AWS::CloudFormation::Stack";
  });

  nestedStacks.forEach(function (f) {
    const fn = template.Resources[f];
    let assetPath = fn.Metadata["aws:asset:path"];
    // get the base name of the asset path file. Trim the .json at the end
    if (
      assetPath.substring(assetPath.length - 5, assetPath.length) === ".json"
    ) {
      assetPath = assetPath.substring(0, assetPath.length - 5);
    }

    fn.Properties.TemplateURL = {
      "Fn::Join": [
        "",
        [
          "https://%%TEMPLATE_BUCKET_NAME%%.s3.",
          {
            Ref: "AWS::URLSuffix",
          },
          "/",
          `%%SOLUTION_NAME%%/%%VERSION%%/${assetPath}`,
        ],
      ],
    };
  });
}

// For each template in global_s3_assets ...
fs.readdirSync(global_s3_assets).forEach((file) => {
  // Import and parse template file
  const raw_template = fs.readFileSync(`${global_s3_assets}/${file}`);
  let template = JSON.parse(raw_template);
  const resources = template.Resources ? template.Resources : {};

  substituteLambdaAssets(template, resources);
  substituteLambdaLayerAssets(template, resources);
  substituteServerlessFunctionAssets(template, resources);
  substituteCDKBucketDeploymentAssets(template, resources);
  substituteCodeCommitRepoAssets(template, resources);
  substituteNestedStackAssets(template, resources);

  // Clean-up parameters section
  const parameters = template.Parameters ? template.Parameters : {};
  const assetParameters = Object.keys(parameters).filter(function (key) {
    return key.includes("AssetParameters");
  });
  assetParameters.forEach(function (a) {
    template.Parameters[a] = undefined;
  });

  // Output modified template file
  const output_template = JSON.stringify(template, null, 2);
  fs.writeFileSync(`${global_s3_assets}/${file}`, output_template);
});
