from fastapi import FastAPI, HTTPException
from sqlalchemy.exc import IntegrityError, OperationalError
import uuid

from models import Cliente, Domicilio, Producto
from db import (
    cliente_insert, cliente_get, cliente_update, cliente_delete,
    domicilio_insert, domicilio_get, domicilio_update, domicilio_delete,
    producto_insert, producto_get, producto_update, producto_delete,
    ClienteORM, DomicilioORM, ProductoORM
)

app = FastAPI(title="Catalogs Service")

@app.post("/clientes", status_code=201)
def crear_cliente(req: Cliente):
    nuevo_id = str(uuid.uuid4())
    nuevo_cliente_orm = ClienteORM(
        clienteID=nuevo_id, razonSocial=req.razon_social,
        nombreComercial=req.nombre_comercial, rfc=req.rfc,
        correoElectronico=req.correo_electronico, telefono=req.telefono
    )
    try:
        cliente_insert(nuevo_cliente_orm)
    except IntegrityError:
        raise HTTPException(status_code=400, detail="Error de integridad")
    return {"clienteID": nuevo_id}

@app.get("/clientes/{clienteID}")
def obtener_cliente(clienteID: str):
    cliente = cliente_get(clienteID)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente

@app.put("/clientes/{clienteID}")
def actualizar_cliente(clienteID: str, req: Cliente):
    if not cliente_get(clienteID):
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    datos_para_db = {
        "razonSocial": req.razon_social, "nombreComercial": req.nombre_comercial,
        "rfc": req.rfc, "correoElectronico": req.correo_electronico, "telefono": req.telefono
    }
    cliente_update(clienteID, datos_para_db)
    return {"status": "ok"}

@app.delete("/clientes/{clienteID}", status_code=204)
def eliminar_cliente(clienteID: str):
    if not cliente_get(clienteID):
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    cliente_delete(clienteID)

# --- CRUD Domicilios ---
@app.post("/domicilios", status_code=201)
def crear_domicilio(req: Domicilio):
    nuevo_id = str(uuid.uuid4())
    nuevo_dom_orm = DomicilioORM(
        domicilioID=nuevo_id, clienteID=req.cliente_id, domicilio=req.domicilio,
        colonia=req.colonia, municipio=req.municipio, estado=req.estado, tipodireccion=req.tipo_direccion
    )
    try:
        domicilio_insert(nuevo_dom_orm)
    except IntegrityError:
        raise HTTPException(status_code=400, detail="El cliente ID no existe")
    return {"domicilioID": nuevo_id}

@app.get("/domicilios/{domicilioID}")
def obtener_domicilio(domicilioID: str):
    domicilio = domicilio_get(domicilioID)
    if not domicilio:
        raise HTTPException(status_code=404, detail="Domicilio no encontrado")
    return domicilio

@app.put("/domicilios/{domicilioID}")
def actualizar_domicilio(domicilioID: str, req: Domicilio):
    if not domicilio_get(domicilioID):
        raise HTTPException(status_code=404, detail="Domicilio no encontrado")
    datos_para_db = {
        "clienteID": req.cliente_id, "domicilio": req.domicilio, "colonia": req.colonia,
        "municipio": req.municipio, "estado": req.estado, "tipodireccion": req.tipo_direccion
    }
    domicilio_update(domicilioID, datos_para_db)
    return {"status": "ok"}

@app.delete("/domicilios/{domicilioID}", status_code=204)
def eliminar_domicilio(domicilioID: str):
    if not domicilio_get(domicilioID):
        raise HTTPException(status_code=404, detail="Domicilio no encontrado")
    domicilio_delete(domicilioID)

# --- CRUD Productos ---
@app.post("/productos", status_code=201)
def crear_producto(req: Producto):
    nuevo_id = str(uuid.uuid4())
    nuevo_prod_orm = ProductoORM(
        productoID=nuevo_id, nombre=req.nombre, unidadMedida=req.unidad_medida, precioBase=req.precio_base
    )
    producto_insert(nuevo_prod_orm)
    return {"productoID": nuevo_id}

@app.get("/productos/{productoID}")
def obtener_producto(productoID: str):
    producto = producto_get(productoID)
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return producto

@app.put("/productos/{productoID}")
def actualizar_producto(productoID: str, req: Producto):
    if not producto_get(productoID):
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    datos_para_db = {"nombre": req.nombre, "unidadMedida": req.unidad_medida, "precioBase": req.precio_base}
    producto_update(productoID, datos_para_db)
    return {"status": "ok"}

@app.delete("/productos/{productoID}", status_code=204)
def eliminar_producto(productoID: str):
    if not producto_get(productoID):
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    producto_delete(productoID)