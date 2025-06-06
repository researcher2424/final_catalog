from __future__ import annotations

import math

from qusi.internal.hadryss_model import LightCurveNetworkBlock
from torch import Tensor
import torch
from torch.nn import (
    Conv1d,
    Module,
    Sigmoid,
    Softmax,
)
from typing_extensions import Self


class HadryssNew(Module):
    """
    A 1D convolutional neural network model for light curve data that will auto-size itself for a given input light
    curve length.
    """

    def __init__(self, *, input_length: int, end_module: Module):
        super().__init__()
        self.input_length: int = input_length
        pooling_sizes, dense_size = self.determine_block_pooling_sizes_and_dense_size()
        self.block0 = LightCurveNetworkBlock(
            input_channels=1,
            output_channels=8,
            kernel_size=3,
            pooling_size=pooling_sizes[0],
        )
        self.block1 = LightCurveNetworkBlock(
            input_channels=8,
            output_channels=8,
            kernel_size=3,
            pooling_size=pooling_sizes[1],
        )
        self.block2 = LightCurveNetworkBlock(
            input_channels=8,
            output_channels=16,
            kernel_size=3,
            pooling_size=pooling_sizes[2],
            batch_normalization=False,
            dropout_rate=0.1,
        )
        self.block3 = LightCurveNetworkBlock(
            input_channels=16,
            output_channels=32,
            kernel_size=3,
            pooling_size=pooling_sizes[3],
            batch_normalization=False,
            dropout_rate=0.1,
        )
        self.block4 = LightCurveNetworkBlock(
            input_channels=32,
            output_channels=64,
            kernel_size=3,
            pooling_size=pooling_sizes[4],
            batch_normalization=False,
            dropout_rate=0.1,
        )
        self.block5 = LightCurveNetworkBlock(
            input_channels=64,
            output_channels=64,
            kernel_size=3,
            pooling_size=pooling_sizes[5],
            batch_normalization=False,
            dropout_rate=0.1,
        )
        self.block6 = LightCurveNetworkBlock(
            input_channels=64,
            output_channels=48,
            kernel_size=3,
            pooling_size=pooling_sizes[6],
            dropout_rate=0.1,
        )
        self.block7 = LightCurveNetworkBlock(
            input_channels=48,
            output_channels=20,
            kernel_size=3,
            pooling_size=pooling_sizes[7],
            dropout_rate=0.1,
            spatial=False,
            length=dense_size + 2,
        )
        self.block8 = LightCurveNetworkBlock(
            input_channels=20,
            output_channels=20,
            kernel_size=dense_size,
            pooling_size=1,
            dropout_rate=0.1,
        )
        self.block9 = LightCurveNetworkBlock(
            input_channels=20, output_channels=20, kernel_size=1, pooling_size=1
        )
        self.end_module = end_module

    def forward(self, x: Tensor) -> Tensor:
        x = x.reshape([-1, 1, self.input_length])
        x = self.block0(x)
        x = self.block1(x)
        x = self.block2(x)
        x = self.block3(x)
        x = self.block4(x)
        x = self.block5(x)
        x = self.block6(x)
        x = self.block7(x)
        x = self.block8(x)
        x = self.block9(x)
        x = self.end_module(x)
        return x

    @classmethod
    def new(cls, input_length: int = 3500, end_module: Module | None = None) -> Self:
        """
        Creates a new Hadryss model.

        :param input_length: The length of the input to auto-size the network to.
        :param end_module: The end module of the network. Defaults to a `HadryssMultiClassEndModule`.
        :return: The model.
        """
        if end_module is None:
            end_module = HadryssMultiClassEndModuleNew.new()
        instance = cls(input_length=input_length, end_module=end_module)
        return instance

    def determine_block_pooling_sizes_and_dense_size(self) -> (list[int], int):
        number_of_pooling_blocks = 8
        pooling_sizes = [1] * number_of_pooling_blocks
        max_dense_final_layer_features = 10
        while True:
            for pooling_size_index, _pooling_size in enumerate(pooling_sizes):
                current_size = self.input_length
                for current_pooling_size in pooling_sizes:
                    current_size -= 2
                    current_size /= current_pooling_size
                    current_size = math.floor(current_size)
                if current_size <= max_dense_final_layer_features:
                    return pooling_sizes, current_size
                pooling_sizes[pooling_size_index] += 1


class HadryssMultiClassEndModuleNew(Module):
    """
    A module for the end of the Hadryss model designed for multiclass classification.
    """

    def __init__(self):
        super().__init__()
        self.prediction_layer = Conv1d(in_channels=20, out_channels=1, kernel_size=1)
        self.sigmoid = Sigmoid()

    def forward(self, x: Tensor) -> Tensor:
        x = self.prediction_layer(x)
        x = self.sigmoid(x)
        x = torch.reshape(x, (-1,))
        return x

    @classmethod
    def new(cls):
        return cls()


class HadryssMultiClassProbabilityEndModuleNew(Module):
    """
    A module for the end of the Hadryss model designed for multi classification.
    """

    def __init__(self, number_of_classes: int):
        super().__init__()
        self.number_of_classes: int = number_of_classes
        self.prediction_layer = Conv1d(in_channels=20, out_channels=self.number_of_classes, kernel_size=1)
        self.soft_max = Softmax(dim=1)

    def forward(self, x: Tensor) -> Tensor:
        x = self.prediction_layer(x)
        x = self.soft_max(x)
        x = torch.reshape(x, (-1, self.number_of_classes))
        return x

    @classmethod
    def new(cls, number_of_classes: int):
        return cls(number_of_classes)


class HadryssMultiClassScoreEndModuleNew(Module):
    """
    A module for the end of the Hadryss model designed for multi classification without softmax.
    """

    def __init__(self, number_of_classes: int):
        super().__init__()
        self.number_of_classes: int = number_of_classes
        self.prediction_layer = Conv1d(in_channels=20, out_channels=self.number_of_classes, kernel_size=1)

    def forward(self, x: Tensor) -> Tensor:
        x = self.prediction_layer(x)
        x = torch.reshape(x, (-1, self.number_of_classes))
        return x

    @classmethod
    def new(cls, number_of_classes: int):
        return cls(number_of_classes)

