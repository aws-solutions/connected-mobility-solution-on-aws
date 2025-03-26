// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { authModuleOAuth2Provider } from "./module";
import { generateUsername } from "./module";

describe("module", () => {
  it("should export oauth2.0 provider module", () => {
    expect(authModuleOAuth2Provider).toBeDefined();
  });

  it("should generate the expected username from a typical email", () => {
    const expectedUsername = "username";
    const email = `${expectedUsername}@example.com`;
    const generatedUsername = generateUsername(email);
    expect(generatedUsername).toBe(expectedUsername);
  });

  it("should generate a hashed, filtered username from an email with invalid values", () => {
    const expectedUsername = "username";
    const originalUsername = `${expectedUsername}$$$$`;
    const email = `${originalUsername}@example.com`;
    const generatedUsernameWithHash = generateUsername(email);
    const [generatedUsername, hash] = generatedUsernameWithHash.split("-");
    expect(generatedUsername).toBe(expectedUsername);
    expect(hash.length).toBe(8);
  });

  it("should generate a hashed, filtered username from an email with invalid values and + signs", () => {
    const expectedUsername1 = "username1";
    const expectedUsername2 = "username2";
    const expectedUsername3 = "username3";
    const originalUsername = `${expectedUsername1}$$$$+${expectedUsername2}+$$$$${expectedUsername3}`;
    const email = `${originalUsername}@example.com`;
    const generatedUsernameWithHash = generateUsername(email);
    const [generatedUsername1, generatedUsername2, generatedUsername3, hash] =
      generatedUsernameWithHash.split("-");
    expect(generatedUsername1).toBe(expectedUsername1);
    expect(generatedUsername2).toBe(expectedUsername2);
    expect(generatedUsername3).toBe(expectedUsername3);
    expect(hash.length).toBe(8);
  });
});
