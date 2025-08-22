from dataclasses import dataclass
from typing import Tuple

from pxr import Gf, UsdGeom, Usd


def conform_camera_vertical_aperture(camera: UsdGeom.Camera, image_resolution: Tuple[float, float]):
    aspect_ratio = image_resolution[0] / image_resolution[1]
    horizontal_aperture = camera.GetHorizontalApertureAttr().Get()
    conformed_vertical_aperature = horizontal_aperture / aspect_ratio
    camera.GetVerticalApertureAttr().Set(conformed_vertical_aperature)


@dataclass
class CameraInfo:

    # Intrinsics
    focal_length: float
    horizontal_aperture: float
    vertical_aperture: float
    near_clip: float
    far_clip: float

    # Extrinsics
    world_to_camera: Tuple[
        float, float, float, float,
        float, float, float, float,
        float, float, float, float,
        float, float, float, float
    ]

    world_to_ndc: Tuple[
        float, float, float, float,
        float, float, float, float,
        float, float, float, float,
        float, float, float, float
    ]

    projection_matrix: Tuple[
        float, float, float, float,
        float, float, float, float,
        float, float, float, float,
        float, float, float, float
    ]

    @staticmethod
    def gf_matrix_to_tuple(matrix: Gf.Matrix4d):
        return tuple([
            value for row in matrix for value in row
        ])

    @classmethod
    def from_usd_camera(cls, camera: UsdGeom.Camera):

        projection_matrix = camera.GetCamera().frustum.ComputeProjectionMatrix()

        # For converting from Z up to Y up
        rotation = Gf.Rotation(Gf.Vec3d(1, 0, 0), -90)
        R = Gf.Matrix4d().SetRotate(rotation)
        camera_prim = camera.GetPrim()
        stage = camera_prim.GetStage()
        up_axis = UsdGeom.GetStageUpAxis(stage)

        # Compute camera to world
        camera_to_world_matrix = UsdGeom.Xformable(camera_prim).ComputeLocalToWorldTransform(Usd.TimeCode.Default())
        if up_axis == UsdGeom.Tokens.z:
            camera_to_world_matrix = camera_to_world_matrix * R
        world_to_camera_matrix = camera_to_world_matrix.GetInverse()
        world_to_ndc = world_to_camera_matrix * projection_matrix

        return cls(
            focal_length=camera.GetFocalLengthAttr().Get(),
            near_clip=camera.GetClippingRangeAttr().Get()[0],
            far_clip=camera.GetClippingRangeAttr().Get()[1],
            horizontal_aperture=camera.GetHorizontalApertureAttr().Get(),
            vertical_aperture=camera.GetVerticalApertureAttr().Get(),
            projection_matrix=cls.gf_matrix_to_tuple(projection_matrix),
            world_to_camera=cls.gf_matrix_to_tuple(world_to_camera_matrix),
            world_to_ndc=cls.gf_matrix_to_tuple(world_to_ndc),
        )
