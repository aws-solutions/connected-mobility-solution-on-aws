// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { useState, useEffect } from "react";

export default function useLocationHash() {
  const [currentPagePath, setCurrentPage] = useState(
    window.location.hash.substring(1),
  );

  useEffect(() => {
    const handler = () => setCurrentPage(window.location.hash.substring(1));
    window.addEventListener("hashchange", handler);
    return () => {};
  }, []);

  useEffect(() => {
    window.scrollTo({ top: 0 });
  }, [currentPagePath]);

  return currentPagePath;
}
