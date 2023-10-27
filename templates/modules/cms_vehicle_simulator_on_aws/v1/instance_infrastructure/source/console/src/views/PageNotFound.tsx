// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { I18n } from "@aws-amplify/core";
import Container from "react-bootstrap/Container";
import Row from "react-bootstrap/Row";
import Col from "react-bootstrap/Col";

/**
 * PageNotFound returns an error when path does not match.
 * @returns Page not found error message
 */
export default function PageNotFound(): React.JSX.Element {
  return (
    <Container>
      <Row>
        <Col>
          <div className="mt-4 p-5 rounded">
            <h3>
              {I18n.get("page.not.found")}:{" "}
              <code>{window.location.pathname}</code>
            </h3>
          </div>
        </Col>
      </Row>
    </Container>
  );
}
