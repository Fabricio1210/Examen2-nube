from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from datetime import datetime

EMAIL_REGEX = r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$'

class Cliente(BaseModel):
    id: Optional[str] = None
    razon_social: str
    nombre_comercial: str
    rfc: str
    correo_electronico: str = Field(..., pattern=r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$')
    telefono: str

class Domicilio(BaseModel):
    id: Optional[str] = None
    cliente_id: str
    domicilio: str
    colonia: str
    municipio: str
    estado: str
    tipo_direccion: Literal["FACTURACION", "ENVIO"]

class Producto(BaseModel):
    id: Optional[str] = None
    nombre: str
    unidad_medida: str
    precio_base: float