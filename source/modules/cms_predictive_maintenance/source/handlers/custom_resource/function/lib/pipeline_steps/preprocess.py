# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

# Standard Library
from typing import Any, Tuple

# Third Party Libraries
import numpy as np
import pandas as pd

np.random.seed(0)


def read_dataset_csv(csv_file_path: str) -> np.ndarray[Any, np.dtype[np.float64]]:
    dataset = pd.read_csv(csv_file_path)
    return dataset.to_numpy()


def split_dataset(
    dataset: np.ndarray[Any, np.dtype[np.float64]],
    train_split_ratio: float,
    validation_split_ratio: float,
) -> Tuple[
    np.ndarray[Any, np.dtype[np.float64]],
    np.ndarray[Any, np.dtype[np.float64]],
    np.ndarray[Any, np.dtype[np.float64]],
]:
    np.random.shuffle(dataset)
    dataset_size = dataset.shape[0]
    (  # pylint: disable=unbalanced-tuple-unpacking
        train_data,
        validation_data,
        test_data,
    ) = np.split(
        dataset,
        [
            int(train_split_ratio * dataset_size),
            int((train_split_ratio + validation_split_ratio) * dataset_size),
        ],
    )

    return train_data, validation_data, test_data


if __name__ == "__main__":
    BASE_DIR = "/opt/ml/processing"
    raw_dataset = read_dataset_csv(csv_file_path=f"{BASE_DIR}/input/dataset.csv")
    train, validation, test = split_dataset(
        dataset=raw_dataset, train_split_ratio=0.7, validation_split_ratio=0.15
    )

    pd.DataFrame(train).to_csv(f"{BASE_DIR}/train/train.csv", header=False, index=False)
    pd.DataFrame(validation).to_csv(
        f"{BASE_DIR}/validation/validation.csv", header=False, index=False
    )
    pd.DataFrame(test).to_csv(f"{BASE_DIR}/test/test.csv", header=False, index=False)
