"""Cloudinary backend — activé quand CLOUDINARY_URL est défini."""
import os
import cloudinary
import cloudinary.uploader

cloudinary.config(cloudinary_url=os.environ.get("CLOUDINARY_URL", ""))


def upload_box(uc: str, file_bytes: bytes) -> str:
    result = cloudinary.uploader.upload(
        file_bytes,
        public_id=f"trigo/box/{uc}",
        format="jpg",
        overwrite=True,
    )
    return result["secure_url"]


def upload_placement(ref: str, file_bytes: bytes) -> str:
    result = cloudinary.uploader.upload(
        file_bytes,
        public_id=f"trigo/placement/{ref}",
        format="jpg",
        overwrite=True,
    )
    return result["secure_url"]
