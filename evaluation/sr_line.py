"""The SR line: the unmodified drone_sr pipeline, called from the LR PNG.

See ../GOALS.md, "固定的退化與放大契約" step 4 and "必須保留的行為與不變式".
Everything here is import and call. drone_sr is not modified, not patched, and
its inference or tiling logic is not copied into this tool. If the evaluation
ever needed behaviour the pipeline does not offer, that is a reason to stop and
report, not a reason to change the pipeline.
"""

from pathlib import Path

from drone_sr.image_io import read_image, write_png
from drone_sr.inference import load_model, upscale

from degradation import SCALE

EXPECTED_SCALE = SCALE


class SuperResolutionLine:
    """The SR model, loaded once and reused for every image in a run."""

    def __init__(self) -> None:
        descriptor = load_model()
        if descriptor.scale != EXPECTED_SCALE:
            # The whole comparison is built on 4x. Making up the difference with
            # a resize would add a transform the contract forbids, so this is a
            # hard failure rather than something to work around.
            raise ValueError(
                f"The evaluation needs a {EXPECTED_SCALE}x model, but models/model.pth is {descriptor.scale}x"
            )
        self._descriptor = descriptor

    @property
    def scale(self) -> int:
        return self._descriptor.scale

    @property
    def device(self):
        return self._descriptor.device

    def run(self, lr_path: Path, destination: Path, expected_size: tuple[int, int]) -> None:
        """LR PNG on disk -> SR PNG, through the pipeline's own public functions.

        *expected_size* is the ground truth's (width, height). A mismatch raises
        rather than resizing: a resize here would make the two lines compare
        different things while every size in the report still looked right.

        Failures carry the source path so a caller looping over a batch can
        record why one image dropped out and carry on. The loop itself belongs
        to the runner, not here.
        """
        image = read_image(lr_path)
        result = upscale(image, self._descriptor)
        height, width = result.shape[-2:]
        if (width, height) != tuple(expected_size):
            raise ValueError(
                f"{lr_path.name}: SR output is {width}x{height}, but the ground truth is "
                f"{expected_size[0]}x{expected_size[1]}"
            )
        # write_png refuses a destination that is the source, so the LR file it
        # just read cannot be clobbered.
        write_png(result, destination, lr_path)
