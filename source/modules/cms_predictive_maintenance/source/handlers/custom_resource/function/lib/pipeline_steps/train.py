# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

# Standard Library
import argparse
import dataclasses

# Third Party Libraries
import torch
from data import (  # type: ignore  # pylint: disable=import-error
    ClassificationData,
    ClassificationDataBatch,
)
from torch import nn
from torch.nn import functional as F
from torch.utils.data import DataLoader

torch.manual_seed(0)


class Model(nn.Module):
    def __init__(self, input_dim: int, output_dim: int) -> None:
        super().__init__()
        num_hidden_units = 128
        self.linear1 = nn.Linear(input_dim, num_hidden_units)
        self.linear2 = nn.Linear(num_hidden_units, num_hidden_units)
        self.linear3 = nn.Linear(num_hidden_units, output_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.linear1(x)
        x = F.relu(x)
        x = self.linear2(x)
        x = F.relu(x)
        x = self.linear3(x)
        x = F.softmax(x)
        return x


@dataclasses.dataclass(frozen=True)
class TrainingHyperparameters:
    batch_size: int
    learning_rate: float
    num_epochs: int


def train(
    train_dataloader: DataLoader[ClassificationDataBatch],
    validation_dataloader: DataLoader[ClassificationDataBatch],
    params: TrainingHyperparameters,
    model: Model,
) -> Model:
    loss_fn = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=params.learning_rate)

    training_losses = []
    training_accuracies = []

    validation_losses = []
    validation_accuracies = []

    for epoch in range(params.num_epochs):
        epoch_train_loss = 0.0
        epoch_validation_loss = 0.0

        epoch_train_accuracies = []
        epoch_validation_accuracies = []

        # training
        for data_batch in train_dataloader:
            pred = model(data_batch["x"])
            loss = loss_fn(pred, data_batch["y"])

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            epoch_train_loss += loss.item()
            epoch_train_accuracies.append(
                float((torch.argmax(pred, dim=1) == data_batch["y"]).float().mean())
            )

        # validation
        with torch.inference_mode():
            for data_batch in validation_dataloader:
                pred = model(data_batch["x"])
                epoch_validation_loss += loss_fn(pred, data_batch["y"]).item()

                epoch_validation_accuracies.append(
                    float((torch.argmax(pred, dim=1) == data_batch["y"]).float().mean())
                )

        training_losses.append(epoch_train_loss)
        validation_losses.append(epoch_validation_loss)

        total_training_accuracy = (
            100 * sum(epoch_train_accuracies) / len(epoch_train_accuracies)
        )
        total_validation_accuracy = (
            100 * sum(epoch_validation_accuracies) / len(epoch_validation_accuracies)
        )
        training_accuracies.append(total_training_accuracy)
        validation_accuracies.append(total_validation_accuracy)

        print(
            f"Epoch: {epoch+1}/{params.num_epochs} Training Accuracy: {total_training_accuracy} %, Validation Accuracy: {total_validation_accuracy} %"
        )

    print("############################# METRICS #############################\n")
    print(f"Training Losses: {training_losses} \n")
    print(f"Validation Losses: {validation_losses} \n")
    print(f"Training Accuracies: {training_accuracies} \n")
    print(f"Validation Accuracies: {validation_accuracies} \n")
    print("###################################################################\n")

    return model


def main(params: TrainingHyperparameters) -> None:
    train_dataset_csv = "/opt/ml/input/data/train/train.csv"
    validation_dataset_csv = "/opt/ml/input/data/validation/validation.csv"
    model_path = "/opt/ml/model/model.pth"

    train_dataset = ClassificationData(train_dataset_csv)
    validation_dataset = ClassificationData(validation_dataset_csv)

    # load dataset
    train_dataloader = DataLoader(
        dataset=train_dataset, batch_size=params.batch_size, shuffle=True
    )
    validation_dataloader = DataLoader(
        dataset=validation_dataset, batch_size=params.batch_size, shuffle=True
    )

    # create model
    model = Model(
        input_dim=train_dataset.num_inputs,
        output_dim=train_dataset.num_classes,
    )
    print(model)

    # train model
    model = train(
        train_dataloader=train_dataloader,
        validation_dataloader=validation_dataloader,
        params=params,
        model=model,
    )

    # save model
    torch.jit.save(torch.jit.script(model), model_path)  # type: ignore[no-untyped-call]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    # hyperparameters sent by the pipeline are passed as command-line arguments to the script.
    parser.add_argument("--num_epochs", type=int, default=100)
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--learning_rate", type=float, default=0.001)

    args = parser.parse_args()

    input_params = TrainingHyperparameters(
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        num_epochs=args.num_epochs,
    )
    print(input_params)

    main(params=input_params)
