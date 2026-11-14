# OV02C10 V4L2 callback API rebase

The camera driver patch adds `ov02c10_get_selection()` with a
`struct v4l2_subdev_client_info *` parameter. The authenticated CachyOS 7.3.1-1
`struct v4l2_subdev_pad_ops.get_selection` callback has no such parameter. The
argument was unused by the function, so it is removed without changing the
reported crop/default/bounds rectangles or any runtime policy.

The initial clean full package build reached `drivers/media/i2c/ov02c10.c` and
failed when assigning the function to `.get_selection`: the function pointer
signatures differed. The local compatibility patch is
[`05a-ov02c10-get-selection-api.patch`](../../../patches/r2/camera/05a-ov02c10-get-selection-api.patch),
inserted immediately after the camera driver patch. SHA-256:
`46c822a422eddb40398cc4b0fe18b03ad82e2ee2fd851dae1aaadbc47b3d5556`.

The patched `drivers/media/i2c/ov02c10.o` compiled successfully with the r2
ARM64 configuration. Its focused log is retained at
`docs/archive/validation/artifacts/sp12-r2-final36-20261113/ov02c10-compile.log`.
This is a local CachyOS 7.3.1 API adaptation; no upstream authorship, sign-off,
or redistribution authorization is claimed.
