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

export function DeleteModal({ campaigns, visible, onDiscard, onDelete }: any) {
  const isMultiple = campaigns.length > 1;
  return (
    <Modal
      visible={visible}
      onDismiss={onDiscard}
      header={isMultiple ? "Delete campaigns" : "Delete campaign"}
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
      {campaigns.length > 0 && (
        <SpaceBetween size="m">
          {isMultiple ? (
            <Box variant="span">
              Permanently delete{" "}
              <Box variant="span" fontWeight="bold">
                {campaigns.length} campaigns
              </Box>
              ? You can’t undo this action.
            </Box>
          ) : (
            <Box variant="span">
              Permanently delete campaign{" "}
              <Box variant="span" fontWeight="bold">
                {campaigns[0].name}
              </Box>
              ? You can’t undo this action.
            </Box>
          )}

          <Alert statusIconAriaLabel="Info">
            Proceeding with this action will disassociate all fleets from the
            {isMultiple ? " campaigns" : " campaign"}
            <Link
              external={true}
              href="#"
              ariaLabel="Learn more about campaign management, opens in new tab"
            >
              Learn more
            </Link>
          </Alert>
        </SpaceBetween>
      )}
    </Modal>
  );
}
