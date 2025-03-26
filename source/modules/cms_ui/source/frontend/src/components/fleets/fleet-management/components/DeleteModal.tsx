// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {
  Alert,
  Box,
  Button,
  Link,
  Modal,
  SpaceBetween,
} from "@cloudscape-design/components";

export function DeleteModal({ fleets, visible, onDiscard, onDelete }: any) {
  const isMultiple = fleets.length > 1;
  return (
    <Modal
      visible={visible}
      onDismiss={onDiscard}
      header={isMultiple ? "Delete fleets" : "Delete fleet"}
      closeAriaLabel="Close dialog"
      footer={
        <Box float="right">
          <SpaceBetween direction="horizontal" size="xs">
            <Button variant="link" onClick={onDiscard}>
              Cancel
            </Button>
            <Button variant="primary" onClick={onDelete} data-testid="submit">
              Delete
            </Button>
          </SpaceBetween>
        </Box>
      }
    >
      {fleets.length > 0 && (
        <SpaceBetween size="m">
          {isMultiple ? (
            <Box variant="span">
              Permanently delete{" "}
              <Box variant="span" fontWeight="bold">
                {fleets.length} fleets
              </Box>
              ? You can’t undo this action.
            </Box>
          ) : (
            <Box variant="span">
              Permanently delete fleet{" "}
              <Box variant="span" fontWeight="bold">
                {fleets[0].id}
              </Box>
              ? You can’t undo this action.
            </Box>
          )}

          <Alert statusIconAriaLabel="Info">
            Proceeding with this action will disassociate all vehicles from the
            {isMultiple ? " fleets" : " fleet"} and will terminate any active
            campaigns.{" "}
            <Link
              external={true}
              href="#"
              ariaLabel="Learn more about fleet management, opens in new tab"
            >
              Learn more
            </Link>
          </Alert>
        </SpaceBetween>
      )}
    </Modal>
  );
}
