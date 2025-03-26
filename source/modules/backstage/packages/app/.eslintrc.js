// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

module.exports = require("@backstage/cli/config/eslint-factory")(__dirname, {
  rules: {
    "react/react-in-jsx-scope": "off", // Safe to turn off in Reactv17+
  },
});
