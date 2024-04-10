// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

// Imports
const fs = require("fs");

// Paths
const globalS3AssetsPath = "../global-s3-assets";

// Substitution constants and functions
const regionalS3AssetsBucketSub = {
  "Fn::Join": [
    "-",
    [
      {
        "Fn::FindInMap": ["Solution", "AssetsConfig", "S3AssetBucketBaseName"],
      },
      {
        "Fn::Sub": "${AWS::Region}",
      },
    ],
  ],
};

function regionalS3AssetsKeySub(assetPath) {
  return {
    "Fn::Join": [
      "/",
      [
        {
          "Fn::FindInMap": ["Solution", "AssetsConfig", "S3AssetKeyPrefix"],
        },
        `${assetPath}`,
      ],
    ],
  };
}

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
      prop.S3Key = regionalS3AssetsKeySub(assetPath);

      // Set the S3 bucket reference
      prop.S3Bucket = regionalS3AssetsBucketSub;
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
      prop.S3Key = regionalS3AssetsKeySub(assetPath);

      // Set the S3 bucket reference
      prop.S3Bucket = regionalS3AssetsBucketSub;
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
      prop.Key = regionalS3AssetsKeySub(assetPath);

      // Set the S3 bucket reference
      prop.Bucket = regionalS3AssetsBucketSub;
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
      prop.SourceObjectKeys = [regionalS3AssetsKeySub(assetPath)];

      // Set the S3 bucket reference
      prop.SourceBucketNames = [regionalS3AssetsBucketSub];
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
      prop.Key = regionalS3AssetsKeySub(assetPath);
      // Set the S3 bucket reference

      prop.Bucket = regionalS3AssetsBucketSub;
    } else {
      console.warn(`No S3Bucket Property found for ${JSON.stringify(prop)}`);
    }
  });
}

function substituteCodePipelineAssets(template, resources) {
  const codePipelines = Object.keys(resources).filter(function (key) {
    return resources[key].Type === "AWS::CodePipeline::Pipeline";
  });
  codePipelines.forEach(function (f) {
    const fn = template.Resources[f];
    let stages;

    if (fn.Properties.hasOwnProperty("Stages")) {
      stages = fn.Properties.Stages;
    }

    stages.forEach(function (s) {
      let actions = s.Actions;
      actions.forEach(function (a) {
        if (
          a.ActionTypeId.Category == "Source" &&
          a.ActionTypeId.Provider == "S3"
        ) {
          a.Configuration.S3Bucket = regionalS3AssetsBucketSub;
        }
      });
    });
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
          "https://",
          regionalS3AssetsBucketSub,
          ".s3.",
          {
            Ref: "AWS::URLSuffix",
          },
          "/",
          regionalS3AssetsKeySub(assetPath),
        ],
      ],
    };
  });
}

function compareJsonKeys(json1, json2) {
  if (typeof json1 !== "object" || typeof json2 !== "object") {
    return false;
  }
  let keys1 = Object.keys(json1).sort();
  let keys2 = Object.keys(json2).sort();

  return JSON.stringify(keys1) === JSON.stringify(keys2);
}

function compareJsonsWithRegex(jsonWithPattern, jsonToMatch) {
  if (
    typeof jsonWithPattern !== "object" ||
    typeof jsonToMatch !== "object" ||
    !compareJsonKeys(jsonWithPattern, jsonToMatch)
  ) {
    return false;
  }

  for (const key in jsonWithPattern) {
    var re = new RegExp(`^${jsonWithPattern[key]}$`);
    if (!re.test(jsonToMatch[key])) {
      return false;
    }
  }

  return true;
}

function replaceSubdict(jsonObj, targetSubdict, replacement) {
  for (const key in jsonObj) {
    if (jsonObj[key] && typeof jsonObj[key] === "object") {
      if (compareJsonsWithRegex(targetSubdict, jsonObj[key])) {
        jsonObj[key] = { ...replacement };
      } else {
        replaceSubdict(jsonObj[key], targetSubdict, replacement);
      }
    }
  }
}

function substitutePolicies(template, resources) {
  const policies = Object.keys(resources).filter(function (key) {
    return resources[key].Type === "AWS::IAM::Policy";
  });
  policies.forEach(function (f) {
    const fn = template.Resources[f];
    let prop;
    if (fn.Properties.hasOwnProperty("PolicyDocument")) {
      prop = fn.Properties.PolicyDocument;
    }

    let cdkBucketRef = {
      "Fn::Sub": "cdk-[a-z0-9]+-assets-.*",
    };

    let customBucketRef = regionalS3AssetsBucketSub;

    replaceSubdict(prop, cdkBucketRef, customBucketRef);
  });
}

function substituteRoles(template, resources) {
  const roles = Object.keys(resources).filter(function (key) {
    return resources[key].Type === "AWS::IAM::Role";
  });
  roles.forEach(function (f) {
    const fn = template.Resources[f];
    let prop;
    if (fn.Properties.hasOwnProperty("Policies")) {
      prop = fn.Properties.Policies;
    }

    let cdkBucketRef = {
      "Fn::Sub": "cdk-[a-z0-9]+-assets-.*",
    };
    let customBucketRef = regionalS3AssetsBucketSub;

    replaceSubdict(prop, cdkBucketRef, customBucketRef);
  });
}

// For each template in globalS3AssetsPath ...
fs.readdirSync(globalS3AssetsPath).forEach((file) => {
  // Import and parse template file
  const rawTemplate = fs.readFileSync(`${globalS3AssetsPath}/${file}`);
  let template = JSON.parse(rawTemplate);
  const resources = template.Resources ? template.Resources : {};

  substituteLambdaAssets(template, resources);
  substituteLambdaLayerAssets(template, resources);
  substituteServerlessFunctionAssets(template, resources);
  substituteCDKBucketDeploymentAssets(template, resources);
  substituteCodeCommitRepoAssets(template, resources);
  substituteNestedStackAssets(template, resources);
  substituteCodePipelineAssets(template, resources);
  substitutePolicies(template, resources);
  substituteRoles(template, resources);

  // Clean-up parameters section
  const parameters = template.Parameters ? template.Parameters : {};
  const assetParameters = Object.keys(parameters).filter(function (key) {
    return key.includes("AssetParameters");
  });
  assetParameters.forEach(function (a) {
    template.Parameters[a] = undefined;
  });

  // Output modified template file
  const outputTemplate = JSON.stringify(template, null, 2);
  fs.writeFileSync(`${globalS3AssetsPath}/${file}`, outputTemplate);
});
