"""Building Blocks for the generator and discriminator."""

import torch
from torch import nn

from img2img.cfg import ActivationType, NormalizationType, PaddingType


class ConvBlock(nn.Module):
    """Convolutional layer + normalization layer + activation layer.

    Args:
        in_channels (int): Number of input channels.
        out_channels (int): Number of output channels.
        kernel_size (int): Kernel size.
        stride (int): Stride.
        padding (int, optional): Padding. Defaults to 0.
        norm (NormalizationType, optional): Normalization type. Defaults to NormalizationType.NONE.
        padding_type (PaddingType, optional): Padding type. Defaults to PaddingType.ZERO.
        activation_type (ActivationType, optional): Act type. Defaults to ActivationType.RELU.
    """

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int,
        stride: int,
        padding: int,
        normalization_type: NormalizationType,
        padding_type: PaddingType,
        activation_type: ActivationType,
        bias=True,
    ) -> None:
        super().__init__()

        self.norm_dim = out_channels

        self.normalization_layer = self._normalization_selector(normalization_type)
        self._activation_layer = self._activation_layer_selector(activation_type)

        self.model = nn.Sequential(
            nn.Conv2d(
                in_channels=in_channels,
                out_channels=out_channels,
                kernel_size=kernel_size,
                stride=stride,
                padding=padding,
                padding_mode=padding_type.value,
                bias=bias,
            ),
            self.normalization_layer,
            self._activation_layer,
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass of the convolutional block.

        Args:
            x (torch.Tensor): Input tensor.

        Returns:
            torch.Tensor: Output tensor.
        """
        x = self.model(x)
        return x

    def _normalization_selector(
        self, normalization_type: NormalizationType
    ) -> nn.Module:
        """Selects the normalization type.

        Args:
            normalization_type (NormalizationType): Normalization type.
            out_channels (int): Number of output channels.

        Raises:
            NotImplementedError: If the normalization type is not implemented.

        Returns:
            nn.Module: Normalization layer.
        """
        if normalization_type == NormalizationType.BATCH:
            return nn.BatchNorm2d(self.norm_dim)
        elif normalization_type == NormalizationType.INSTANCE:
            return nn.InstanceNorm2d(self.norm_dim)
        elif normalization_type == NormalizationType.LAYER:
            return nn.LayerNorm(self.norm_dim)
        # TODO: add adain
        elif normalization_type == NormalizationType.NONE:
            return nn.Identity()
        else:
            raise NotImplementedError(
                f"Normalization type {normalization_type} is not implemented."
            )

    def _activation_layer_selector(self, activation_type: ActivationType) -> nn.Module:
        """Selects the activation type.

        Args:
            activation_type (ActivationType): Activation type.

        Raises:
            NotImplementedError: If the activation type is not implemented.

        Returns:
            nn.Module: Activation layer.
        """
        if activation_type == ActivationType.RELU:
            return nn.ReLU(inplace=True)
        elif activation_type == ActivationType.LEAKY_RELU:
            return nn.LeakyReLU(0.2, inplace=True)
        elif activation_type == ActivationType.TANH:
            return nn.Tanh()
        elif activation_type == ActivationType.SIGMOID:
            return nn.Sigmoid()
        elif activation_type == ActivationType.NONE:
            return nn.Identity()
        else:
            raise NotImplementedError(
                f"Activation type {activation_type} is not implemented."
            )


class ConvBlocks(nn.Module):
    """Stack ConvBlock on sequentially starting with in_channels=layer_multiplier until out_channels=max_layer_multiplier.
    The channel size is doubled in each ConvBlock.

    Args:
        layer_multiplier (int): Number of channels multiplier.
        max_layer_multiplier (int): Maximum channels number.
        kernel_size (int): Kernel size.
        stride (int): Stride.
        padding (int, optional): Padding. Defaults to 0.
        padding_type (PaddingType, optional): Padding type. Defaults to PaddingType.ZERO.
        activation_type (ActivationType, optional): Act type. Defaults to ActivationType.RELU.
    """

    def __init__(
        self,
        layer_multiplier: int = 64,
        max_layer_multiplier: int = 1024,
        kernel_size: int = 4,
        stride: int = 2,
        padding: int = 0,
        padding_type: PaddingType = PaddingType.ZERO,
        normalization_type: NormalizationType = NormalizationType.NONE,
        activation_type: ActivationType = ActivationType.RELU,
    ) -> None:
        super().__init__()

        self.layers = []
        layer_multiplier = layer_multiplier

        while layer_multiplier < max_layer_multiplier:
            self.layers.append(
                ConvBlock(
                    layer_multiplier,
                    layer_multiplier * 2,
                    kernel_size=kernel_size,
                    stride=stride,
                    padding=padding,
                    padding_type=padding_type,
                    normalization_type=normalization_type,
                    activation_type=activation_type,
                )
            )
            layer_multiplier *= 2

        self.model = nn.Sequential(*self.layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass of the convolutional blocks.

        Args:
            x (torch.Tensor): Input tensor.

        Returns:
            torch.Tensor: Output tensor.
        """
        x = self.model(x)
        return x


class ResBlock(nn.Module):
    """Residual block.

    Args:
        channels (int): Number of channels.
        kernel_size (int): Kernel size.
        stride (int): Stride.
        padding (int, optional): Padding. Defaults to 0.
        padding_type (PaddingType, optional): Padding type. Defaults to PaddingType.ZERO.
        activation_type (ActivationType, optional): Act type. Defaults to ActivationType.RELU.
    """

    def __init__(
        self,
        channels: int = 256,
        kernel_size=3,
        stride: int = 1,
        padding: int = 1,
        normalization_type=NormalizationType.INSTANCE,
        padding_type=PaddingType.ZERO,
        activation_type=ActivationType.RELU,
    ) -> None:
        super().__init__()

        self.model = nn.Sequential(
            ConvBlock(
                in_channels=channels,
                out_channels=channels,
                kernel_size=kernel_size,
                stride=stride,
                padding=padding,
                normalization_type=normalization_type,
                padding_type=padding_type,
                activation_type=activation_type,
            ),
            ConvBlock(
                in_channels=channels,
                out_channels=channels,
                kernel_size=kernel_size,
                stride=stride,
                padding=padding,
                normalization_type=normalization_type,
                padding_type=padding_type,
                activation_type=ActivationType.NONE,
            ),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass of the residual block.

        Args:
            x (torch.Tensor): Input tensor.

        Returns:
            torch.Tensor: Output tensor.
        """
        x = self.model(x) + x
        return x


class ResBlocks(nn.Module):
    """Residual blocks.

    Args:
        channels (int): Number of channels.
        repeat_num (int): Number of times to repeat the ResBlocks.
    """

    def __init__(
        self,
        channels: int = 256,
        num_blocks: int = 4,
        normalization_type: NormalizationType = NormalizationType.INSTANCE,
        padding_type: PaddingType = PaddingType.ZERO,
        activation_type: ActivationType = ActivationType.RELU,
    ) -> None:
        super().__init__()

        self.layers = []

        for _ in range(num_blocks):
            self.layers.append(
                ResBlock(
                    channels=channels,
                    normalization_type=normalization_type,
                    padding_type=padding_type,
                    activation_type=activation_type,
                )
            )

        self.model = nn.Sequential(*self.layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass of the residual blocks.

        Args:
            x (torch.Tensor): Input tensor.

        Returns:
            torch.Tensor: Output tensor.
        """
        x = self.model(x)
        return x


# if __name__ == "__main__":
# TODO: Add tests for checking the shapes of the block outputs.
# print("\n\n")
# print("ConvBlock ============================", end="\n\n")
# print(ConvBlock(3, 64, 4, 2,0,NormalizationType.NONE), (3, 256, 256))
# print("\n\n")
# print("ConvBlocks ===========================", end="\n\n")
# print(ConvBlocks(), (3, 256, 256))
# print("\n\n")
# print("ResBlock =============================", end="\n\n")
# print(ResBlock(), (256, 256, 256))
# print("\n\n")
# print("ResBlocks ============================", end="\n\n")
# print(ResBlocks(), (256, 256, 256))
