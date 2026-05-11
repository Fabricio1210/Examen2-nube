from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
import uuid, io, os, json, hashlib
import httpx, boto3
from dotenv import load_dotenv

load_dotenv()

from models import NotaVentaConContenido
from db import (
    nota_insert, nota_get,
    contenido_insert, contenido_get_by_nota,
    NotaVentaORM, ContenidoNotaORM,
)
from S3 import s3_upload_pdf, s3_get_pdf_bytes, s3_marcar_descargada
from pdf_gen import generate_nota_pdf

# ──────────────────────────────────────────
# Variables de entorno
# ──────────────────────────────────────────
ENVIRONMENT          = os.environ.get("ENVIRONMENT", "local")
CATALOGS_SERVICE_URL = os.environ.get("CATALOGS_SERVICE_URL", "http://127.0.0.1:8001")
BASE_URL             = os.environ.get("BASE_URL", "http://localhost:8002")
SQS_QUEUE_URL        = os.environ.get("SQS_QUEUE_URL")
AWS_REGION           = os.environ.get("AWS_REGION", "us-east-1")

# ──────────────────────────────────────────
# Cliente SQS
# ──────────────────────────────────────────
def get_sqs():
    return boto3.client("sqs", region_name=AWS_REGION)


def publicar_notificacion(correo: str, folio: str, enlace_descarga: str) -> None:
    payload = {"correo": correo, "folio": folio, "enlace_descarga": enlace_descarga}

    get_sqs().send_message(
        QueueUrl    = SQS_QUEUE_URL,
        MessageBody = json.dumps(payload),
        MessageAttributes={
            "folio": {
                "DataType":    "String",
                "StringValue": folio,
            },
            "ambiente": {
                "DataType":    "String",
                "StringValue": ENVIRONMENT,
            },
        },
    )


# ──────────────────────────────────────────
# App
# ──────────────────────────────────────────
app = FastAPI(title="Notas de Venta Service")


@app.post("/notas", status_code=201)
async def crear_nota(req: NotaVentaConContenido):
    nota_p    = req.nota
    contenido = req.contenido

    async with httpx.AsyncClient() as client:
        res_cli = await client.get(f"{CATALOGS_SERVICE_URL}/clientes/{nota_p.cliente_id}")
        if res_cli.status_code != 200:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        cliente_data = res_cli.json()

        res_df = await client.get(f"{CATALOGS_SERVICE_URL}/domicilios/{nota_p.direccion_facturacion_id}")
        res_de = await client.get(f"{CATALOGS_SERVICE_URL}/domicilios/{nota_p.direccion_envio_id}")
        if res_df.status_code != 200 or res_de.status_code != 200:
            raise HTTPException(status_code=404, detail="Domicilio no válido")

    nueva_nota_id   = str(uuid.uuid4())
    total_acumulado = 0.0
    items_pdf       = []
    items_contenido = []   # acumulamos primero, insertamos después

    async with httpx.AsyncClient() as client:
        for item in contenido:
            res_p = await client.get(f"{CATALOGS_SERVICE_URL}/productos/{item.producto_id}")
            if res_p.status_code != 200:
                raise HTTPException(status_code=404, detail=f"Producto {item.producto_id} no existe")

            producto = res_p.json()
            importe  = item.cantidad * item.precio_unitario
            total_acumulado += importe

            items_contenido.append(ContenidoNotaORM(
                notaVentaID    = nueva_nota_id,
                productoID     = item.producto_id,
                cantidad       = item.cantidad,
                precioUnitario = item.precio_unitario,
                importe        = importe,
            ))
            items_pdf.append({
                "nombreProducto": producto["nombre"],
                "cantidad":       item.cantidad,
                "precioUnitario": item.precio_unitario,
                "importe":        importe,
            })

    # Primero la nota (padre), luego el contenido (hijos)
    nota_insert(NotaVentaORM(
        notaVentaID            = nueva_nota_id,
        clienteID              = nota_p.cliente_id,
        domicilioFacturacionID = nota_p.direccion_facturacion_id,
        domicilioEnvioID       = nota_p.direccion_envio_id,
        folio                  = nota_p.folio,
        total                  = total_acumulado,
    ))

    for item_orm in items_contenido:
        contenido_insert(item_orm)

    try:
        pdf_bytes = generate_nota_pdf(
            cliente_data,
            {"folio": nota_p.folio, "total": total_acumulado},
            items_pdf,
        )
        s3_upload_pdf(pdf_bytes, cliente_data["rfc"], nota_p.folio)
    except Exception as e:
        print(f"Error S3: {e}")

    try:
        enlace_descarga = f"{BASE_URL}/notas/{nueva_nota_id}/descargar"
        publicar_notificacion(cliente_data["correoElectronico"], nota_p.folio, enlace_descarga)
    except Exception as e:
        print(f"Error SQS: {e}")

    return {
        "notaVentaID": nueva_nota_id,
        "folio":       nota_p.folio,
        "total":       total_acumulado,
        "status":      "Procesado",
    }


@app.get("/notas/{notaVentaID}")
def leer_nota(notaVentaID: str):
    nota = nota_get(notaVentaID)
    if not nota:
        raise HTTPException(status_code=404, detail="Nota no encontrada")
    contenido = contenido_get_by_nota(notaVentaID)
    return {
        "notaVentaID":            nota.notaVentaID,
        "folio":                  nota.folio,
        "clienteID":              nota.clienteID,
        "domicilioFacturacionID": nota.domicilioFacturacionID,
        "domicilioEnvioID":       nota.domicilioEnvioID,
        "total":                  nota.total,
        "contenido": [
            {
                "productoID":     i.productoID,
                "cantidad":       i.cantidad,
                "precioUnitario": i.precioUnitario,
                "importe":        i.importe,
            }
            for i in contenido
        ],
    }


@app.get("/notas/{notaVentaID}/descargar")
def descargar_nota(notaVentaID: str):
    nota = nota_get(notaVentaID)
    if not nota:
        raise HTTPException(status_code=404, detail="Nota no encontrada")

    with httpx.Client() as client:
        res     = client.get(f"{CATALOGS_SERVICE_URL}/clientes/{nota.clienteID}")
        cliente = res.json()

    s3_marcar_descargada(cliente["rfc"], nota.folio)
    pdf_bytes = s3_get_pdf_bytes(cliente["rfc"], nota.folio)
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={nota.folio}.pdf"},
    )