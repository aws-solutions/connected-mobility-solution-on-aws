// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { useEffect, useState } from "react";

export const useSplitPanel = (
  selectedItems,
  defaultOpenState = false,
  defaultSize = 300,
) => {
  const [splitPanelSize, setSplitPanelSize] = useState(defaultSize);
  const [splitPanelOpen, setSplitPanelOpen] = useState(defaultOpenState);
  const [hasManuallyClosedOnce, setHasManuallyClosedOnce] = useState(false);

  const onSplitPanelResize = ({ detail: { size } }) => {
    setSplitPanelSize(size);
  };

  const onSplitPanelToggle = ({ detail: { open } }) => {
    setSplitPanelOpen(open);

    if (!open) {
      setHasManuallyClosedOnce(true);
    }
  };

  useEffect(() => {
    if (selectedItems.length && !hasManuallyClosedOnce) {
      setSplitPanelOpen(true);
    }
  }, [selectedItems.length, hasManuallyClosedOnce]);

  return {
    splitPanelOpen,
    onSplitPanelToggle,
    splitPanelSize,
    onSplitPanelResize,
  };
};
