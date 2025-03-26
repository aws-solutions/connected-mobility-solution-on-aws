// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React from "react";
import Modal from "@cloudscape-design/components/modal";
import Box from "@cloudscape-design/components/box";

export const DynamicModal = ({
  title = "Modal Title",
  content = {
    type: "text",
    data: "Default text content",
  },
  visible,
  setVisible,
}: any) => {
  const renderContent = () => {
    switch (content.type) {
      case "text":
        return <Box variant="p">{content.data}</Box>;
      case "image":
        return (
          <Box>
            <img
              src={content.data}
              style={{
                maxWidth: "100%",
                maxHeight: "500px",
                objectFit: "contain",
              }}
            />
          </Box>
        );
      case "video":
        return (
          <Box textAlign="center">
            <video
              controls
              style={{
                maxWidth: "100%",
                maxHeight: "500px",
                objectFit: "contain",
              }}
            >
              <source src={content.data} />
              Your browser does not support the video tag.
            </video>
          </Box>
        );
      default:
        return <Box variant="p">Invalid content type</Box>;
    }
  };

  return (
    <Modal
      visible={visible}
      onDismiss={() => setVisible(false)}
      header={title}
      size="large"
    >
      {renderContent()}
    </Modal>
  );
};
