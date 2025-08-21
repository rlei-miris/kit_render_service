# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

from pathlib import Path
from pydantic import BaseModel, Field
from typing import Tuple

import omni.kit.commands
import omni.usd
from omni.services.core.routers import ServiceAPIRouter
import omni.replicator.core as rep

from pxr import UsdGeom

router = ServiceAPIRouter(tags=["Miris Render Server Extension"])


class OpenStageModel(BaseModel):
    usd_file_location: str = Field(
        default="/tmp/scene.usd",
        title="USD File Location",
        description="Location of the USD file to open",
    )


@router.post(
    "/open_stage",
    summary="Open a USD file",
    description="An endpoint to open a USD file as the active stage",
)
async def open_stage(open_stage_data: OpenStageModel):
    print("[miris_render_server_ext] /open_stage was called")

    # Open the usd file
    usd_context = omni.usd.get_context()
    usd_context.open_stage(open_stage_data.usd_file_location)

    # Set to path traced
    rep.settings.set_render_pathtraced()

    msg = f"[miris_render_server_ext] Opened stage: {open_stage_data.usd_file_location}"
    print(msg)
    return msg


class RenderModel(BaseModel):

    camera_name: str = Field(
        default="camera_0",
        title="Camera Name",
        description="Name of the camera",
    )

    camera_position: Tuple[float, float, float] = Field(
        default=(0, 0, 0),
        title="Camera Position",
        description="Position of the camera",
    )

    camera_rotation: Tuple[float, float, float] = Field(
        default=(0, 0, 0),
        title="Camera Rotation",
        description="Rotation of the camera",
    )

    camera_focal_length: float = Field(
        default=15,
        title="Camera Focal Length",
        description="Focal length of the camera",
    )

    camera_horizontal_aperture: float = Field(
        default=20,
        title="Camera Focal Length",
        description="Focal length of the camera",
    )

    image_resolution: Tuple[float, float] = Field(
        default=(1024, 1024),
        title="Output image resolution",
        description="Output image resolution",
    )


@router.post(
    "/render",
    summary="Render from a camera position",
    description="An endpoint render from a camera position",
)
async def render(render_data: RenderModel):
    print(f"[miris_render_server_ext] /render was called with args: {render_data}")

    # Create the hydra render product
    camera = rep.create.camera(
        position=render_data.camera_position,
        rotation=render_data.camera_rotation,
        focal_length=render_data.camera_focal_length,
        horizontal_aperture=render_data.camera_horizontal_aperture,
        name=render_data.camera_name,
    )

    render_product = rep.create.render_product(
        camera,
        resolution=render_data.image_resolution,
        name=render_data.camera_name,
    )

    with rep.trigger.on_frame(max_execs=1):
        pass

    # Initialize and attach writer
    writer = rep.WriterRegistry.get("BasicWriter")
    writer.initialize(
        output_dir=f"_output_{render_data.camera_name}",
        rgb=True,
        distance_to_image_plane=True,
        colorize_depth=True,
    )
    writer.attach([render_product])

    # Execute the tasks asynchronously
    rep.orchestrator.run()

    msg = f"[miris_render_server_ext] Rendered camera {render_data.camera_name}"
    print(msg)
    return msg
