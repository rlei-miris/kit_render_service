# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

import os
import tempfile
from pathlib import Path
from pydantic import BaseModel, Field
from typing import Tuple

import omni.kit.commands
import omni.usd
from omni.services.core.routers import ServiceAPIRouter
import omni.replicator.core as rep

from pxr import UsdGeom

router = ServiceAPIRouter(tags=["Miris Render Server Extension"])


class OpenStageRequestData(BaseModel):
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
async def open_stage(request_data: OpenStageRequestData):
    print("[miris_render_server_ext] /open_stage was called")

    # Open the usd file
    usd_context = omni.usd.get_context()
    usd_context.open_stage(request_data.usd_file_location)

    # Set to path traced
    rep.settings.set_render_pathtraced()

    msg = f"[miris_render_server_ext] Opened stage: {request_data.usd_file_location}"
    print(msg)
    return msg


class RenderRequestData(BaseModel):

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


class RenderResponseData(BaseModel):

    color_image_path: str = Field(title="Output color image path")
    depth_image_path: str = Field(title="Output depth image path")
    depth_npy_path: str = Field(title="Output depth npy path")


@router.post(
    "/render",
    summary="Render from a camera position",
    description="An endpoint render from a camera position",
    response_model=RenderResponseData,
)
async def render(request_data: RenderRequestData):
    print(f"[miris_render_server_ext] /render was called with args: {request_data}")

    # Create the hydra render product
    camera = rep.create.camera(
        position=request_data.camera_position,
        rotation=request_data.camera_rotation,
        focal_length=request_data.camera_focal_length,
        horizontal_aperture=request_data.camera_horizontal_aperture,
        name=request_data.camera_name,
    )

    render_product = rep.create.render_product(
        camera,
        resolution=request_data.image_resolution,
        name=request_data.camera_name,
    )

    with rep.trigger.on_frame(max_execs=1):
        pass

    # Initialize and attach writer
    writer = rep.WriterRegistry.get("BasicWriter")
    tmp_dir = tempfile.mkdtemp()
    output_dir = os.path.join(tmp_dir, f"output_{request_data.camera_name}")
    writer.initialize(
        output_dir=output_dir,
        rgb=True,
        distance_to_image_plane=True,
        colorize_depth=True,
    )

    writer.attach([render_product])

    # Execute the tasks, wait for completion
    await rep.orchestrator.run_until_complete_async()

    # Collect artifacts
    # TODO: Is there a way to query where the Replicator writer is saving the files?
    color_image_path = os.path.join(output_dir, "rgb_0000.png")
    depth_image_path = os.path.join(output_dir, "distance_to_image_plane_0000.png")
    depth_npy_path = os.path.join(output_dir, "distance_to_image_plane_0000.npy")
    for file_path in (color_image_path, depth_image_path, depth_npy_path):
        assert os.path.isfile(file_path), f"Expected {file_path} to exist"

    return RenderResponseData(
        color_image_path=color_image_path,
        depth_image_path=depth_image_path,
        depth_npy_path=depth_npy_path,
    )
