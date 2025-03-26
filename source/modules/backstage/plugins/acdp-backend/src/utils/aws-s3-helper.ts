// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import createLimiter from "p-limit";
import recursiveReadDir from "recursive-readdir";
import path from "path";
import fs from "fs";

import {
  PutObjectCommandInput,
  DeleteObjectCommand,
  ListObjectsV2Command,
  ListObjectsV2CommandOutput,
  S3Client,
} from "@aws-sdk/client-s3";
import { Upload } from "@aws-sdk/lib-storage";

import { LoggerService } from "@backstage/backend-plugin-api/index";
import { Entity, DEFAULT_NAMESPACE } from "@backstage/catalog-model";

import { awsApiCallWithErrorHandling } from "./error-handling-helper";

// Perform rate limited generic operations by passing a function and a list of arguments
const bulkStorageOperation = async <T>(
  operation: (arg: T) => Promise<unknown>,
  args: T[],
  { concurrencyLimit } = { concurrencyLimit: 25 },
) => {
  const limiter = createLimiter(concurrencyLimit);
  await Promise.all(args.map((arg) => limiter(operation, arg)));
};

export class AwsS3Helper {
  private readonly s3Client: S3Client;
  private readonly bucketName: string;
  private readonly logger: LoggerService;
  private readonly sse?: "aws:kms" | "AES256";

  constructor(options: {
    s3Client: S3Client;
    bucketName: string;
    logger: LoggerService;
    sse?: "aws:kms" | "AES256";
  }) {
    this.s3Client = options.s3Client;
    this.bucketName = options.bucketName;
    this.logger = options.logger;
    this.sse = options.sse;
  }

  async getAllObjectsFromBucket(keyPrefix: string = ""): Promise<string[]> {
    const objects: string[] = [];
    let nextContinuation: string | undefined;
    let allObjects: ListObjectsV2CommandOutput;
    // Iterate through every file in the root of the publisher.
    do {
      const command = new ListObjectsV2Command({
        Bucket: this.bucketName,
        ContinuationToken: nextContinuation,
        ...(keyPrefix ? { Prefix: keyPrefix } : {}),
      });
      allObjects = await awsApiCallWithErrorHandling(
        () => this.s3Client.send(command),
        `Could not list objects from bucket name: ${this.bucketName}`,
        this.logger,
      );
      objects.push(
        ...(allObjects.Contents || [])
          .map((f) => f.Key || "")
          .filter((f) => !!f),
      );
      nextContinuation = allObjects.NextContinuationToken;
    } while (nextContinuation);

    return objects;
  }

  async deleteObjectsFromBucket(objectsToDelete: string[]) {
    await bulkStorageOperation(
      async (relativeFilePath) => {
        return await awsApiCallWithErrorHandling(
          () =>
            this.s3Client.send(
              new DeleteObjectCommand({
                Bucket: this.bucketName,
                Key: relativeFilePath,
              }),
            ),
          `Could not delete object from bucket name: ${this.bucketName} with key: ${relativeFilePath}`,
          this.logger,
        );
      },
      objectsToDelete,
      { concurrencyLimit: 10 },
    );
  }

  async uploadFilesToBucket(
    entity: Entity,
    localDirectoryPath: string,
    s3Prefix: string,
  ) {
    try {
      const fileList = await recursiveReadDir(localDirectoryPath).catch(
        (error: Error) => {
          throw new Error(
            `Failed to read fetched content directory: ${error.message}`,
          );
        },
      );

      await bulkStorageOperation(
        async (absoluteFilePath: string) => {
          const relativeFilePath = path.relative(
            localDirectoryPath,
            absoluteFilePath,
          );
          const fileStream = fs.createReadStream(absoluteFilePath);

          const params: PutObjectCommandInput = {
            Bucket: this.bucketName,
            Key: path.posix.join(s3Prefix, relativeFilePath),
            Body: fileStream,
            ...(this.sse && { ServerSideEncryption: this.sse }),
          };

          const upload = new Upload({
            client: this.s3Client,
            params,
          });
          return upload.done();
        },
        fileList,
        { concurrencyLimit: 10 },
      );

      this.logger.info(
        `Successfully uploaded all the generated files for Entity ${entity.metadata.name}. Total number of files: ${fileList.length}`,
      );
    } catch (error: any) {
      const errorMessage = "Unable to upload file(s) to AWS S3.";
      this.logger.error(`${errorMessage} Error: ${error}`);
      throw new Error(errorMessage);
    }
  }
}

/**
 * Takes a posix path and returns a lower-cased version of entity's triplet
 * with the remaining path in posix.
 *
 * Path must not include a starting slash.
 *
 * @example
 * lowerCaseEntityTriplet('default/Component/backstage')
 * // return default/component/backstage
 */
const lowerCaseEntityTriplet = (posixPath: string): string => {
  const [namespace, kind, name, ...rest] = posixPath.split(path.posix.sep);
  const lowerNamespace = namespace.toLowerCase();
  const lowerKind = kind.toLowerCase();
  const lowerName = name.toLowerCase();
  return [lowerNamespace, lowerKind, lowerName, ...rest].join(path.posix.sep);
};

export const getCloudPathForLocalPath = (
  entity: Entity,
  localPath = "",
  externalStorageRootPath = "",
): string => {
  const relativeFilePathPosix = localPath.split(path.sep).join(path.posix.sep);

  const entityRootDir = `${entity.metadata?.namespace ?? DEFAULT_NAMESPACE}/${
    entity.kind
  }/${entity.metadata.name}`;

  const relativeFilePathTriplet = `${entityRootDir}/${relativeFilePathPosix}`;

  const destination = lowerCaseEntityTriplet(relativeFilePathTriplet);

  const destinationWithRoot = [
    ...externalStorageRootPath.split(path.posix.sep).filter((s) => s !== ""),
    destination,
  ].join("/");

  return destinationWithRoot;
};
