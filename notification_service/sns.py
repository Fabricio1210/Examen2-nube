import boto3
from fastapi import HTTPException
from dotenv import load_dotenv
import os

load_dotenv()

SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN")


def sns_client():
    return boto3.client("sns", region_name="us-east-1")


def sns_mandar_nota(correo: str, folio: str, enlace_descarga: str) -> None:
    client = sns_client()
    mensaje = (
        f"Se ha generado tu nota de venta con folio: {folio}.\n\n"
        f"Descarga tu nota aqui:\n{enlace_descarga}"
    )
    try:
        client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=mensaje,
            Subject=f"Nota de venta {folio}",
            MessageAttributes={
                "correo": {"DataType": "String", "StringValue": correo}
            }
        )
    except Exception as e:
        print(f"Error SNS: {e}")
        raise HTTPException(status_code=500, detail="Error al notificar")