"""KRC Frame Router: routes a frame batch by its length. One frame goes to `image`,
several go to `video`; the other output sends None.

Made for MiniMax H3 "Reference to Video": wire `image` into a reference image input and
`video` into a reference video input, and a still or a clip from the same Resizer reaches
the right one. That node accepts None on the unused side, and its reference video input
takes IMAGE frames (tested 2026-10-26).

IMAGE in, IMAGE out; one console line per run. `images` is optional: with nothing coming in
(e.g. a disabled or muted Resizer before it) both outputs send None, so the target runs
without this reference. Standalone: it uses nothing from KRC NodePack. A V3 node. Promoted
from the dev repo's "KRC Frame Redirector" on 2026-10-29.
"""

from comfy_api.latest import io

NODE_ID = "KRC Frame Router"
TAG = "[KRC Frame Router]"


def route(frames):
    """Which output gets the frames: "image" for one frame, else "video"."""
    return "image" if frames <= 1 else "video"


class KRCFrameRouter(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id=NODE_ID,
            display_name=NODE_ID,
            category="KRC NodePack Extras",
            description=("One frame goes to `image`, several go to `video`; the other output sends None. "
                         "Wire both into H3 Reference to Video's image / video reference inputs."),
            inputs=[io.Image.Input("images", optional=True,
                                   tooltip="A frame or a frame batch, e.g. from KRC Resizer. Nothing in: both outputs send None.")],
            outputs=[io.Image.Output(display_name="image"), io.Image.Output(display_name="video")],
        )

    @classmethod
    def execute(cls, images=None):
        if images is None:
            print(f"{TAG} no input -> no reference")
            return io.NodeOutput(None, None)
        frames = int(images.shape[0]) if hasattr(images, "shape") and len(images.shape) == 4 else 1
        target = route(frames)
        print(f"{TAG} {frames} frame{'' if frames == 1 else 's'} -> {target}")
        return io.NodeOutput(images, None) if target == "image" else io.NodeOutput(None, images)


NODE_CLASS_MAPPINGS = {"KRC Frame Router": KRCFrameRouter}
NODE_DISPLAY_NAME_MAPPINGS = {"KRC Frame Router": "KRC Frame Router"}
