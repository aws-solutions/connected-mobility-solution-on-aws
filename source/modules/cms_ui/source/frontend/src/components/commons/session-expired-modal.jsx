// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {
  Box,
  Modal,
  Button,
  SpaceBetween,
  Alert,
} from "@cloudscape-design/components";

export function SessionExpiredModal({ visible, onRefresh }) {
  return (
    visible && (
      <Modal
        onDismiss={onRefresh}
        visible={visible}
        header="Session Expired"
        footer={
          <Box float="right">
            <SpaceBetween direction="horizontal" size="xs">
              <Button
                ariaLabel="Login Again"
                onClick={onRefresh}
                data-testid="login-again-button"
              >
                Login Again
              </Button>
            </SpaceBetween>
          </Box>
        }
        data-testid="login-expired-warning-modal"
      >
        <Alert type="warning">
          Your session has expired. You will be returned to the login page to
          reauthenticate.
        </Alert>
      </Modal>
    )
  );
}
