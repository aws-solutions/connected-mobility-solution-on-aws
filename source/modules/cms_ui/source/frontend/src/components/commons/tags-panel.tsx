// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React, { useState } from "react";
import {
  Container,
  Header,
  TagEditor,
  TagEditorProps,
  NonCancelableCustomEvent,
} from "@cloudscape-design/components";
import { InfoLink } from "./info-link";

export const tagEditorI18nStrings = {
  tagLimit: (availableTags: number) =>
    `You can add up to ${availableTags} more tag${
      availableTags > 1 ? "s" : ""
    }.`,
  addButton: "Add new tag",
};

interface TagsPanelProps {
  loadHelpPanelContent: any;
  inputData: any;
  setInputData: any;
}

export function TagsPanel({
  loadHelpPanelContent,
  inputData,
  setInputData,
}: TagsPanelProps) {
  const [tags, setTags] = useState<TagEditorProps.Tag[]>(
    (inputData?.tags || []).map((tag) => ({
      key: tag.Key,
      value: tag.Value,
    })) || [],
  );

  const onChange = ({
    detail,
  }: NonCancelableCustomEvent<TagEditorProps.ChangeDetail>) => {
    setTags((detail.tags as TagEditorProps.Tag[]) || []);
    if (detail.valid) {
      setInputData({
        tags: detail.tags
          .filter((tag) => !tag.existing)
          .map((tag) => ({ Key: tag.key, Value: tag.value })),
      });
    }
  };

  return (
    <Container
      id="tags-panel"
      header={
        <Header
          variant="h2"
          info={<InfoLink onFollow={() => loadHelpPanelContent(10)} />}
          description="A tag is a label that you assign to an AWS resource. Each tag consists of a key and an optional value. You can use tags to search and filter your resources or track your AWS costs."
        >
          Tags
        </Header>
      }
    >
      <TagEditor
        tags={tags}
        onChange={onChange}
        keysRequest={() => Promise.resolve([])}
        valuesRequest={() => Promise.resolve([])}
        i18nStrings={tagEditorI18nStrings}
      />
    </Container>
  );
}
