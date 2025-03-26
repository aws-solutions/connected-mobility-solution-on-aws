// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { Application } from "@aws-sdk/client-service-catalog-appregistry";

import { Entity } from "@backstage/catalog-model";

export class MockAcdpMetricsApi {
  async getApplication(): Promise<Application> {
    return {
      arn: "arn:aws:servicecatalog:us-east-2:111111111111:/applications/test-application-id",
    };
  }
}

export const mockMetricsEntity: Entity = {
  apiVersion: "backstage.io/v1alpha1",
  kind: "Component",
  metadata: {
    uid: "uniqueId",
    annotations: {
      "aws.amazon.com/acdp-deploy-on-create": "true",
      "aws.amazon.com/acdp-deployment-target-account": "111111111111",
      "aws.amazon.com/acdp-deployment-target-region": "us-east-2",
      "aws.amazon.com/techdocs-builder": "external",
      "backstage.io/techdocs-ref": "dir:.",
      "aws.amazon.com/template-entity-ref": "template:default/cms-sample",
      "aws.amazon.com/acdp-assets-ref": "dir:assets",
      "backstage.io/source-location":
        "url:https://test-bucket.s3.us-west-2.amazonaws.com/local/backstage/catalog/acdp/component/cms-sample/assets",
    },
    description:
      "A CDK Python app for showing a basic skeleton for a CMS module",
    name: "cms-sample",
    namespace: "acdp-metrics",
  },
  spec: {
    lifecycle: "experimental",
    owner: "group:default/mock",
    type: "service",
  },
};
