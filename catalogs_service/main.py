from fastapi import FastAPI, HTTPException
from sqlalchemy.exc import IntegrityError
import uuid, os, time, boto3
from dotenv import load_dotenv

load_dotenv()

from models import Cliente, Domicilio, Producto
from db import (
    cliente_insert, cliente_get, cliente_update, cliente_delete,
    domicilio_insert, domicilio_get, domicilio_update, domicilio_delete,
    producto_insert, producto_get, producto_update, producto_delete,
    ClienteORM, DomicilioORM, ProductoORM,
)

ENVIRONMENT = os.environ.get("ENVIRONMENT", "local")
AWS_REGION  = os.environ.get("AWS_REGION", "us-east-1")
NAMESPACE   = "Examen2/CatalogsService"   # namespace en CloudWatch

def get_cw():
    return boto3.client("cloudwatch", region_name=AWS_REGION)


def put_metric(metric_name: str, value: float, unit: str, dimensions: list):
    """Manda una métrica a CloudWatch. Falla silenciosamente para no afectar el servicio."""
    try:
        get_cw().put_metric_data(
            Namespace  = NAMESPACE,
            MetricData = [{
                "MetricName": metric_name,
                "Value":      value,
                "Unit":       unit,
                "Dimensions": dimensions,
            }]
        )
    except Exception as e:
        print(f"[CloudWatch] Error mandando métrica: {e}")


def dimensions(endpoint: str):
    """Dimensiones comunes: ambiente + endpoint."""
    return [
        {"Name": "Environment", "Value": ENVIRONMENT},
        {"Name": "Endpoint",    "Value": endpoint},
    ]


def track(endpoint: str):
    def decorator(fn):
        start      = time.time()
        status_range = "2xx"
        try:
            result = fn()
            return result
        except HTTPException as e:
            status_range = "4xx" if e.status_code < 500 else "5xx"
            raise
        except Exception as e:
            status_range = "5xx"
            raise
        finally:
            duration_ms = (time.time() - start) * 1000
            dims = dimensions(endpoint)
            # Métrica 1 – latencia
            put_metric("RequestDuration", duration_ms, "Milliseconds", dims)
            # Métrica 2 – conteo por rango HTTP
            put_metric(f"HttpRequests{status_range}", 1, "Count", dims)
    return decorator


app = FastAPI(title="Catalogs Service")


@app.post("/clientes", status_code=201)
def crear_cliente(req: Cliente):
    def _():
        nuevo_id = str(uuid.uuid4())
        orm = ClienteORM(
            clienteID=nuevo_id, razonSocial=req.razon_social,
            nombreComercial=req.nombre_comercial, rfc=req.rfc,
            correoElectronico=req.correo_electronico, telefono=req.telefono,
        )
        try:
            cliente_insert(orm)
        except IntegrityError:
            raise HTTPException(status_code=400, detail="Error de integridad")
        except Exception:
            raise HTTPException(status_code=500, detail="Error interno")
        return {"clienteID": nuevo_id}
    return track("/clientes")(_)


@app.get("/clientes/{clienteID}")
def obtener_cliente(clienteID: str):
    def _():
        cliente = cliente_get(clienteID)
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        return cliente
    return track("/clientes/{clienteID}")(_)


@app.put("/clientes/{clienteID}")
def actualizar_cliente(clienteID: str, req: Cliente):
    def _():
        if not cliente_get(clienteID):
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        datos = {
            "razonSocial": req.razon_social, "nombreComercial": req.nombre_comercial,
            "rfc": req.rfc, "correoElectronico": req.correo_electronico, "telefono": req.telefono,
        }
        try:
            cliente_update(clienteID, datos)
        except IntegrityError:
            raise HTTPException(status_code=400, detail="RFC ya en uso")
        return {"status": "ok"}
    return track("/clientes/{clienteID}")(_)


@app.delete("/clientes/{clienteID}", status_code=204)
def eliminar_cliente(clienteID: str):
    def _():
        if not cliente_get(clienteID):
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        cliente_delete(clienteID)
    return track("/clientes/{clienteID}")(_)

@app.post("/domicilios", status_code=201)
def crear_domicilio(req: Domicilio):
    def _():
        nuevo_id = str(uuid.uuid4())
        orm = DomicilioORM(
            domicilioID=nuevo_id, clienteID=req.cliente_id,
            domicilio=req.domicilio, colonia=req.colonia,
            municipio=req.municipio, estado=req.estado,
            tipodireccion=req.tipo_direccion,
        )
        try:
            domicilio_insert(orm)
        except IntegrityError:
            raise HTTPException(status_code=400, detail="El cliente_id no existe")
        except Exception:
            raise HTTPException(status_code=500, detail="Error de conexión")
        return {"domicilioID": nuevo_id}
    return track("/domicilios")(_)


@app.get("/domicilios/{domicilioID}")
def obtener_domicilio(domicilioID: str):
    def _():
        dom = domicilio_get(domicilioID)
        if not dom:
            raise HTTPException(status_code=404, detail="Domicilio no encontrado")
        return dom
    return track("/domicilios/{domicilioID}")(_)


@app.put("/domicilios/{domicilioID}")
def actualizar_domicilio(domicilioID: str, req: Domicilio):
    def _():
        if not domicilio_get(domicilioID):
            raise HTTPException(status_code=404, detail="Domicilio no encontrado")
        datos = {
            "clienteID": req.cliente_id, "domicilio": req.domicilio,
            "colonia": req.colonia, "municipio": req.municipio,
            "estado": req.estado, "tipodireccion": req.tipo_direccion,
        }
        try:
            domicilio_update(domicilioID, datos)
        except IntegrityError:
            raise HTTPException(status_code=400, detail="cliente_id no válido")
        except Exception:
            raise HTTPException(status_code=500, detail="Error al actualizar")
        return {"status": "ok"}
    return track("/domicilios/{domicilioID}")(_)


@app.delete("/domicilios/{domicilioID}", status_code=204)
def eliminar_domicilio(domicilioID: str):
    def _():
        if not domicilio_get(domicilioID):
            raise HTTPException(status_code=404, detail="Domicilio no encontrado")
        domicilio_delete(domicilioID)
    return track("/domicilios/{domicilioID}")(_)

@app.post("/productos", status_code=201)
def crear_producto(req: Producto):
    def _():
        nuevo_id = str(uuid.uuid4())
        orm = ProductoORM(
            productoID=nuevo_id, nombre=req.nombre,
            unidadMedida=req.unidad_medida, precioBase=req.precio_base,
        )
        try:
            producto_insert(orm)
            return {"productoID": nuevo_id}
        except Exception:
            raise HTTPException(status_code=500, detail="Error al crear producto")
    return track("/productos")(_)


@app.get("/productos/{productoID}")
def obtener_producto(productoID: str):
    def _():
        prod = producto_get(productoID)
        if not prod:
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        return prod
    return track("/productos/{productoID}")(_)


@app.put("/productos/{productoID}")
def actualizar_producto(productoID: str, req: Producto):
    def _():
        if not producto_get(productoID):
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        datos = {
            "nombre": req.nombre,
            "unidadMedida": req.unidad_medida,
            "precioBase": req.precio_base,
        }
        try:
            producto_update(productoID, datos)
        except Exception:
            raise HTTPException(status_code=500, detail="Error al actualizar")
        return {"status": "ok"}
    return track("/productos/{productoID}")(_)


@app.delete("/productos/{productoID}", status_code=204)
def eliminar_producto(productoID: str):
    def _():
        if not producto_get(productoID):
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        producto_delete(productoID)
    return track("/productos/{productoID}")(_)