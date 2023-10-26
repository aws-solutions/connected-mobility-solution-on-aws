// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import sanitizeHtml from 'sanitize-html';
import React from 'react';

const defaultOptions = {
  allowedTags: ['b', 'i', 'em', 'strong', 'a', 'p'],
  allowedAttributes: {
    a: ['href'],
  },
  allowedIframeHostnames: [],
};

const sanitize = (dirty: string, options: any) => ({
  __html: sanitizeHtml(
    dirty,
    { ...defaultOptions, ...options } || defaultOptions,
  ),
});

export interface SanitizedProps {
  text: string;
}

export const Sanitized = ({ text }: SanitizedProps) => (
  <span dangerouslySetInnerHTML={sanitize(text, {})} />
);
