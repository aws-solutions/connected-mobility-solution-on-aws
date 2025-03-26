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

export function DeleteModal({ vehicles, visible, onDiscard, onDelete }: any) {
  const isMultiple = vehicles.length > 1;
  return (
    <Modal
      visible={visible}
      onDismiss={onDiscard}
      header={isMultiple ? "Delete vehicles" : "Delete vehicle"}
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
      {vehicles.length > 0 && (
        <SpaceBetween size="m">
          {isMultiple ? (
            <Box variant="span">
              Permanently delete{" "}
              <Box variant="span" fontWeight="bold">
                {vehicles.length} vehicles
              </Box>
              ? You can’t undo this action.
            </Box>
          ) : (
            <Box variant="span">
              Permanently delete vehicle{" "}
              <Box variant="span" fontWeight="bold">
                {vehicles[0].id}
              </Box>
              ? You can’t undo this action.
            </Box>
          )}

          <Alert statusIconAriaLabel="Info">
            Proceeding with this action will disassociate all fleets from the
            {isMultiple ? " vehicles" : " vehicle"} and will terminate any
            active vehicle specific campaigns.{" "}
            <Link
              external={true}
              href="#"
              ariaLabel="Learn more about vehicle management, opens in new tab"
            >
              Learn more
            </Link>
          </Alert>
        </SpaceBetween>
      )}
    </Modal>
  );
}
