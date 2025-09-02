import uuid
import boto3
from botocore.client import Config
from app.config import Config as cfg

s3 = boto3.client(
    's3',
    endpoint_url=cfg.YANDEX_ENDPOINT,
    aws_access_key_id=cfg.YANDEX_ACCESS_KEY,
    aws_secret_access_key=cfg.YANDEX_SECRET_KEY,
    config=Config(signature_version='s3v4'),
    region_name='ru-central1'
)

#Загрузка изображения в облако
def upload_image_to_yandex(file, filename: str) -> str:
    # Уникальное имя, чтобы избежать коллизий
    key = f"menu_images/{uuid.uuid4()}_{filename}"

    # Загружаем файл
    s3.upload_fileobj(file, cfg.YANDEX_BUCKET_NAME, key, ExtraArgs={"ACL": "public-read"})

    # Публичная ссылка на файл
    return f"{cfg.YANDEX_ENDPOINT}/{cfg.YANDEX_BUCKET_NAME}/{key}"