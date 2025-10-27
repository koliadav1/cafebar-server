import uuid
import aioboto3
from botocore.client import Config
from app.config import Config as cfg

session = aioboto3.Session()

# Загрузка изображения в облако
async def upload_image_to_yandex(file, filename: str) -> str:
    key = f"menu_images/{uuid.uuid4()}_{filename}"

    async with session.client(
        's3',
        endpoint_url=cfg.YANDEX_ENDPOINT,
        aws_access_key_id=cfg.YANDEX_ACCESS_KEY,
        aws_secret_access_key=cfg.YANDEX_SECRET_KEY,
        config=Config(signature_version='s3v4'),
        region_name='ru-central1'
    ) as s3:
        if hasattr(file, 'read'):
            file_content = file.read()
        else:
            file_content = file
            
        await s3.put_object(
            Bucket=cfg.YANDEX_BUCKET_NAME,
            Key=key,
            Body=file_content,
            ACL='public-read'
        )
    
    return f"{cfg.YANDEX_ENDPOINT}/{cfg.YANDEX_BUCKET_NAME}/{key}"