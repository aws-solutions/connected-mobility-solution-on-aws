// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React, { useCallback, useState } from "react";
import { FlashbarProps } from "@cloudscape-design/components";

type NotificationActionType = "create" | "delete";
type NotificationStatusType = "success" | "in-progress" | "error";

type Notification = {
  id: string | undefined;
  action: NotificationActionType;
  status: NotificationStatusType;
  message: string;
};

export default function useNotifications() {
  const [notifications, setNotifications] = useState<Array<any>>([]);

  const dismissNotification = useCallback((id: string) => {
    setNotifications((notifications) =>
      notifications.filter((notification) => notification.id !== id),
    );
  }, []);

  const updateOrAdd = useCallback(
    (notification: FlashbarProps.MessageDefinition) => {
      setNotifications((notifications) => {
        const existingItemIndex = notifications.findIndex(
          (item) => item.id === notification.id,
        );
        if (existingItemIndex === -1) {
          // Notification with the same id does not exist, add it
          return [notification, ...notifications];
        } else {
          // Notification with the same id already exists, update it
          const newArray = [...notifications];
          newArray.splice(existingItemIndex, 1, notification);
          return newArray;
        }
      });
    },
    [],
  );

  const notify = useCallback(
    (notifications: Notification[]) => {
      notifications.map((notif) => {
        const messageId = `${notif.action}-${notif.id}-notification`;
        const content = notif.message;

        updateOrAdd({
          type: notif.status === "in-progress" ? "info" : notif.status,
          dismissible: notif.status !== "in-progress",
          statusIconAriaLabel: notif.status,
          dismissLabel: "Dismiss message",
          content,
          id: messageId,
          onDismiss: () => dismissNotification(messageId),
        });
      });
    },
    [dismissNotification, updateOrAdd],
  );

  return {
    notifications,
    notify,
  };
}
