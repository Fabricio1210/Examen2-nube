import boto3
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

BUCKET = os.environ.get("S3_BUCKET_NAME")


def s3_client():
    return boto3.client("s3", region_name="us-east-1")


def s3_upload_pdf(pdf_bytes: bytes, rfc: str, folio: str) -> None:
    key = f"{rfc}/{folio}.pdf"
    s3_client().put_object(
        Bucket=BUCKET,
        Key=key,
        Body=pdf_bytes,
        ContentType="application/pdf",
        Metadata={
            "hora-envio":       datetime.utcnow().isoformat(),
            "nota-descargada":  "false",
            "veces-enviado":    "1"
        }
    )


def s3_get_metadata(rfc: str, folio: str) -> dict:
    key = f"{rfc}/{folio}.pdf"
    response = s3_client().head_object(Bucket=BUCKET, Key=key)
    return response["Metadata"]


def s3_update_metadata(rfc: str, folio: str, metadata: dict) -> None:
    key = f"{rfc}/{folio}.pdf"
    s3_client().copy_object(
        Bucket=BUCKET,
        Key=key,
        CopySource={"Bucket": BUCKET, "Key": key},
        Metadata=metadata,
        MetadataDirective="REPLACE",
        ContentType="application/pdf"
    )


def s3_increment_envio(rfc: str, folio: str) -> None:
    metadata = s3_get_metadata(rfc, folio)
    metadata["hora-envio"] = datetime.utcnow().isoformat()
    metadata["veces-enviado"] = str(int(metadata["veces-enviado"]) + 1)
    s3_update_metadata(rfc, folio, metadata)


def s3_marcar_descargada(rfc: str, folio: str) -> None:
    metadata = s3_get_metadata(rfc, folio)
    metadata["nota-descargada"] = "true"
    s3_update_metadata(rfc, folio, metadata)


def s3_get_pdf_bytes(rfc: str, folio: str) -> bytes:
    key = f"{rfc}/{folio}.pdf"
    response = s3_client().get_object(Bucket=BUCKET, Key=key)
    return response["Body"].read()


def s3_get_object(key: str) -> bytes:
    s3 = boto3.client("s3")
    bucket_name = "752929-esi3898k-examen1"
    try:
        response = s3.get_object(Bucket=bucket_name, Key=key)
        return response['Body'].read()
    except Exception as e:
        print(f"Error S3 Get: {e}")
        raise e