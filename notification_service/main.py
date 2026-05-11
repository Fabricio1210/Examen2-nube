
from fastapi import FastAPI
from contextlib import asynccontextmanager
import asyncio, boto3, json, os
from dotenv import load_dotenv
from sns import sns_mandar_nota

load_dotenv()

SQS_QUEUE_URL = os.environ.get("SQS_QUEUE_URL")
AWS_REGION    = os.environ.get("AWS_REGION", "us-east-1")
ENVIRONMENT   = os.environ.get("ENVIRONMENT", "local")


_folios_procesados: set[str] = set()

def ya_procesado(folio: str) -> bool:
    return folio in _folios_procesados

def marcar_procesado(folio: str) -> None:
    _folios_procesados.add(folio)

def get_sqs():
    return boto3.client("sqs", region_name=AWS_REGION)



async def sqs_worker():
    print(f"[{ENVIRONMENT}] Worker SQS iniciado. Cola: {SQS_QUEUE_URL}")
    sqs = get_sqs()

    while True:
        try:
            resp = sqs.receive_message(
                QueueUrl              = SQS_QUEUE_URL,
                MaxNumberOfMessages   = 10,
                WaitTimeSeconds       = 5,
                MessageAttributeNames = ["All"],
            )

            for msg in resp.get("Messages", []):
                receipt = msg["ReceiptHandle"]
                try:
                    body  = json.loads(msg["Body"])
                    folio = body["folio"]

                    if ya_procesado(folio):
                        print(f"[{ENVIRONMENT}] Duplicado ignorado → folio={folio}")
                        sqs.delete_message(QueueUrl=SQS_QUEUE_URL, ReceiptHandle=receipt)
                        continue

                    sns_mandar_nota(
                        correo          = body["correo"],
                        folio           = folio,
                        enlace_descarga = body["enlace_descarga"],
                    )

                    marcar_procesado(folio)
                    sqs.delete_message(QueueUrl=SQS_QUEUE_URL, ReceiptHandle=receipt)
                    print(f"[{ENVIRONMENT}] Notificación enviada → folio={folio}")

                except Exception as e:
                    print(f"[{ENVIRONMENT}] Error procesando mensaje: {e}")

        except Exception as e:
            print(f"[{ENVIRONMENT}] Error en polling SQS: {e}")

        await asyncio.sleep(1)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(sqs_worker())
    yield
    task.cancel()


app = FastAPI(title="Microservicio de Notificaciones", lifespan=lifespan)


@app.get("/health")
def health_check():
    return {"status": "ok", "ambiente": ENVIRONMENT}