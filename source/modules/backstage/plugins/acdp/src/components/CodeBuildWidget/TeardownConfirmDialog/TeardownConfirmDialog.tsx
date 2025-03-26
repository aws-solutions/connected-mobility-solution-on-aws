// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0
/*
 * Copyright 2021 The Backstage Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
import { useCallback, useState } from "react";

import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  makeStyles,
} from "@material-ui/core";
import Alert from "@material-ui/lab/Alert";

import { Entity } from "@backstage/catalog-model";
import { alertApiRef, useApi } from "@backstage/core-plugin-api";
import { Progress, ResponseErrorPanel } from "@backstage/core-components";
import { assertError } from "@backstage/errors";

import { useTeardownConfirmDialogState } from "./useTeardownConfirmDialogState";

const useStyles = makeStyles({
  advancedButton: {
    fontSize: "0.7em",
  },
  dialogActions: {
    display: "inline-block",
  },
});

export const TeardownConfirmDialogContent = ({
  entity,
  onConfirm,
  onClose,
}: {
  entity: Entity;
  onConfirm: () => any;
  onClose: () => any;
}) => {
  const alertApi = useApi(alertApiRef);
  const classes = useStyles();
  const state = useTeardownConfirmDialogState(entity);
  const [busy, setBusy] = useState(false);

  const onTeardown = useCallback(
    async function onTeardownFn() {
      if ("teardownEntity" in state) {
        setBusy(true);
        try {
          state.teardownEntity();
          onConfirm();
        } catch (err) {
          assertError(err);
          alertApi.post({ message: err.message });
        } finally {
          setBusy(false);
        }
      }
    },
    [alertApi, onConfirm, state],
  );

  if (state.type === "loading") {
    return <Progress />;
  }

  if (state.type === "error") {
    return <ResponseErrorPanel error={state.error} />;
  }

  if (state.type === "teardown") {
    return (
      <>
        <DialogContentText>
          This action will run the teardown build for the following entity:
        </DialogContentText>
        <DialogContentText component="ul">
          <li>{state.entityRef}</li>
        </DialogContentText>
        <DialogContentText>
          To redeploy, you must unregister and then re-create the entity.
        </DialogContentText>
        <Box marginTop={2}>
          <Button
            variant="contained"
            color="secondary"
            disabled={busy}
            onClick={onTeardown}
          >
            Confirm
          </Button>
          <DialogActions className={classes.dialogActions}>
            <Button onClick={onClose} color="primary">
              Cancel
            </Button>
          </DialogActions>
        </Box>
      </>
    );
  }

  return <Alert severity="error">Internal error: Unknown state</Alert>;
};

export type TeardownConfirmDialogProps = {
  open: boolean;
  onConfirm: () => any;
  onClose: () => any;
  entity: Entity;
};

export const TeardownConfirmDialog = (props: TeardownConfirmDialogProps) => {
  const { open, onConfirm, onClose, entity } = props;
  return (
    <Dialog open={open} onClose={onClose}>
      <DialogTitle id="teardown-confirm-dialog-title">
        Are you sure you want to teardown resources for this entity?
      </DialogTitle>
      <DialogContent>
        <TeardownConfirmDialogContent
          entity={entity}
          onConfirm={onConfirm}
          onClose={onClose}
        />
      </DialogContent>
    </Dialog>
  );
};
