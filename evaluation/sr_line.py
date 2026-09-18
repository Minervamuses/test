"""The SR line: the unmodified drone_sr pipeline, called from the LR PNG.

See ../GOALS.md, "固定的退化與放大契約" step 4 and "必須保留的行為與不變式".
Everything here is import and call. drone_sr is not modified, not patched, and
its inference or tiling logic is not copied into this tool. If the evaluation
ever needed behaviour the pipeline does not offer, that is a reason to stop and
report, not a reason to change the pipeline.
"""

from drone_sr.inference import load_model

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
