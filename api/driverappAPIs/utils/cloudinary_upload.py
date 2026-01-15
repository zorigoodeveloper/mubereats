import cloudinary.uploader

def upload_worker_image(file, worker_id):
    result = cloudinary.uploader.upload(
        file,
        folder="workers",
        public_id=f"worker_{worker_id}",
        overwrite=True,
        resource_type="image",
        fetch_format="auto",
        quality="auto",
    )
    return result["secure_url"]
