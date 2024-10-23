# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

# Standard Library
from typing import TypedDict

# Third Party Libraries
import pandas as pd
import torch
from torch.utils.data import Dataset


class ClassificationDataBatch(TypedDict):
    x: torch.Tensor
    y: torch.Tensor


class ClassificationData(Dataset[ClassificationDataBatch]):
    def __init__(self, csv_file_path: str) -> None:
        df = pd.read_csv(csv_file_path).astype(float)
        dataset = df.to_numpy()
        x = dataset[:, :-1]
        y = dataset[:, -1]

        self.x = torch.tensor(x, dtype=torch.float32)
        self.y = torch.tensor(y, dtype=torch.int64)
        self.num_data_points = self.x.shape[0]
        self.num_inputs = self.x.shape[1]
        self.num_classes = len(torch.unique(self.y))

    def __getitem__(self, index: int) -> ClassificationDataBatch:
        return ClassificationDataBatch(x=self.x[index], y=self.y[index])

    def __len__(self) -> int:
        return self.num_data_points
