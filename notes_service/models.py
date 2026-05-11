from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from datetime import datetime

class ContenidoNota(BaseModel):
    id: Optional[str] = None
    producto_id: str
    cantidad: int
    precio_unitario: float
    importe: Optional[float] = 0.0

class NotaVenta(BaseModel):
    id: Optional[str] = None
    folio: str
    cliente_id: str
    direccion_facturacion_id: str
    direccion_envio_id: str
    total: Optional[float] = 0.0
    fecha_creacion: datetime

class NotaVentaConContenido(BaseModel):
    nota: NotaVenta
    contenido: List[ContenidoNota]