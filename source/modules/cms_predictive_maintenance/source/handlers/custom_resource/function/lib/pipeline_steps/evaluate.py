# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import json
import pathlib
import tarfile

# Third Party Libraries
import torch
from data import ClassificationData  # type: ignore  # pylint: disable=import-error
from torch.utils.data import DataLoader


def main() -> None:
    model_dir = "/opt/ml/processing/model"
    model_zip_path = f"{model_dir}/model.tar.gz"
    extracted_model_path = f"{model_dir}/model.pth"

    test_dataset_path = "/opt/ml/processing/test/test.csv"
    evaluation_report_dir = "/opt/ml/processing/evaluation"
    evaluation_report_file_path = "/opt/ml/processing/evaluation/evaluation.json"

    files_to_extract = ["model.pth"]
    with tarfile.open(model_zip_path, "r:gz") as tar:
        for file_name in files_to_extract:
            tar.extract(file_name, model_dir)

    model = torch.jit.load(extracted_model_path)  # type: ignore[no-untyped-call]
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    test_dataloader = DataLoader(
        dataset=ClassificationData(test_dataset_path),
        batch_size=32,
    )

    accuracies = []
    with torch.inference_mode():
        for data_batch in test_dataloader:
            pred = model(data_batch["x"].to(device))
            accuracies.append(
                float((torch.argmax(pred, dim=1) == data_batch["y"]).float().mean())
            )
    accuracy = sum(accuracies) / len(accuracies)
    print(f"Accuracy of the model on the test dataset: {100*accuracy:.2f}%")

    evaluation_report = {
        "binary_classification_metrics": {
            "accuracy": {
                "value": accuracy,
                "standard_deviation": "NaN",
            },
        },
    }

    pathlib.Path(evaluation_report_dir).mkdir(parents=True, exist_ok=True)
    with open(evaluation_report_file_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(evaluation_report))


if __name__ == "__main__":
    main()
