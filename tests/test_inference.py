import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import torch
from spandrel import Architecture, ImageModelDescriptor, SizeRequirements

from drone_sr.inference import load_model, upscale


def synthetic_descriptor(*, wrong_size=False, channels=3, scale=2):
    """An untrained toy model exercises the real descriptor, not SR quality."""
    model = torch.nn.Conv2d(channels, channels, 1)

    def forward(module, tensor):
        if torch.is_grad_enabled():
            raise AssertionError("Inference must disable gradients")
        if module.training:
            raise AssertionError("Inference must use eval mode")
        parameter = next(module.parameters())
        if tensor.device != parameter.device or tensor.dtype != parameter.dtype:
            raise AssertionError("Tensor and model device/dtype must match")
        result = tensor.repeat_interleave(scale, -2).repeat_interleave(scale, -1)
        return result[..., :-1, :] if wrong_size else result

    return ImageModelDescriptor(
        model,
        model.state_dict(),
        architecture=Mock(spec=Architecture),
        purpose="SR",
        tags=[],
        supports_half=False,
        supports_bfloat16=False,
        scale=scale,
        input_channels=channels,
        output_channels=channels,
        size_requirements=SizeRequirements(minimum=4, multiple_of=4),
        call_fn=forward,
    )


class InferenceTests(unittest.TestCase):
    def test_real_descriptor_pads_odd_input_and_removes_padding(self):
        descriptor = synthetic_descriptor()
        source = torch.arange(45, dtype=torch.float32).reshape(1, 3, 3, 5) / 44
        output = upscale(source, descriptor)
        self.assertEqual(output.shape, (1, 3, 6, 10))
        torch.testing.assert_close(output, source.repeat_interleave(2, -2).repeat_interleave(2, -1))

    def test_wrong_output_size_is_rejected(self):
        descriptor = synthetic_descriptor(wrong_size=True)
        with self.assertRaisesRegex(ValueError, "output shape"):
            upscale(torch.zeros(1, 3, 4, 4), descriptor)

    def test_missing_checkpoint_has_actionable_error(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch("drone_sr.inference.MODEL_PATH", Path(directory) / "model.pth"):
                with self.assertRaisesRegex(FileNotFoundError, "SR model not found: models/model.pth"):
                    load_model()

    def test_invalid_checkpoint_fails_through_real_loader(self):
        with tempfile.TemporaryDirectory() as directory:
            checkpoint = Path(directory) / "invalid.pth"
            checkpoint.write_bytes(b"not a checkpoint")
            with patch("drone_sr.inference.MODEL_PATH", checkpoint):
                with self.assertRaisesRegex(RuntimeError, "Unable to load SR model"):
                    load_model()

    def test_loader_selects_cpu_and_converts_descriptor_to_float32(self):
        descriptor = synthetic_descriptor().to(dtype=torch.float64)
        with tempfile.TemporaryDirectory() as directory:
            checkpoint = Path(directory) / "model.pth"
            checkpoint.touch()
            with (
                patch("drone_sr.inference.MODEL_PATH", checkpoint),
                patch("drone_sr.inference.ModelLoader") as loader,
                patch("drone_sr.inference.torch.cuda.is_available", return_value=False),
            ):
                loader.return_value.load_from_file.return_value = descriptor
                loaded = load_model()
                loader.return_value.load_from_file.assert_called_once_with(checkpoint)
        self.assertEqual(loaded.device, torch.device("cpu"))
        self.assertEqual(loaded.dtype, torch.float32)
        self.assertFalse(loaded.model.training)

    def test_non_image_and_non_rgb_descriptors_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            checkpoint = Path(directory) / "model.pth"
            checkpoint.touch()
            for descriptor in (object(), synthetic_descriptor(channels=1)):
                with self.subTest(descriptor=type(descriptor).__name__):
                    with (
                        patch("drone_sr.inference.MODEL_PATH", checkpoint),
                        patch("drone_sr.inference.ModelLoader") as loader,
                    ):
                        loader.return_value.load_from_file.return_value = descriptor
                        with self.assertRaisesRegex(ValueError, "RGB super-resolution"):
                            load_model()


if __name__ == "__main__":
    unittest.main()
