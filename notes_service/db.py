from sqlalchemy import create_engine, Column, String, Float, Integer, Enum, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from typing import Optional, List
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")

engine = create_engine(
    DATABASE_URL,
    connect_args={"ssl": {"fake_config": True}}
)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class ClienteORM(Base):
    __tablename__ = "Cliente"

    clienteID         = Column(String(36),  primary_key=True)
    razonSocial       = Column(String(100), nullable=False)
    nombreComercial   = Column(String(100), nullable=False)
    rfc               = Column(String(20),  nullable=False)
    correoElectronico = Column(String(100), nullable=False)
    telefono          = Column(String(20),  nullable=False)

    notas = relationship("NotaVentaORM", back_populates="cliente")


class DomicilioORM(Base):
    __tablename__ = "Domicilio"

    domicilioID   = Column(String(36),  primary_key=True)
    clienteID     = Column(String(36),  ForeignKey("Cliente.clienteID"), nullable=False)
    domicilio     = Column(String(100), nullable=False)
    colonia       = Column(String(100), nullable=False)
    municipio     = Column(String(100), nullable=False)
    estado        = Column(String(100), nullable=False)
    tipodireccion = Column(Enum("FACTURACION", "ENVIO"), nullable=False)


class ProductoORM(Base):
    __tablename__ = "Producto"

    productoID   = Column(String(36),  primary_key=True)
    nombre       = Column(String(100), nullable=False)
    unidadMedida = Column(String(100), nullable=False)
    precioBase   = Column(Float,       nullable=False)


class NotaVentaORM(Base):
    __tablename__ = "NotaVenta"

    notaVentaID            = Column(String(36),  primary_key=True)
    clienteID              = Column(String(36),  ForeignKey("Cliente.clienteID"),     nullable=False)
    domicilioFacturacionID = Column(String(36),  ForeignKey("Domicilio.domicilioID"), nullable=False)
    domicilioEnvioID       = Column(String(36),  ForeignKey("Domicilio.domicilioID"), nullable=False)
    folio                  = Column(String(100), nullable=False, unique=True)
    total                  = Column(Float,       nullable=False)

    cliente   = relationship("ClienteORM",      back_populates="notas")
    contenido = relationship("ContenidoNotaORM", back_populates="nota")


class ContenidoNotaORM(Base):
    __tablename__ = "ContenidoNota"

    notaVentaID    = Column(String(36), ForeignKey("NotaVenta.notaVentaID"), primary_key=True)
    productoID     = Column(String(36), ForeignKey("Producto.productoID"),   primary_key=True)
    cantidad       = Column(Integer, nullable=False)
    precioUnitario = Column(Float,   nullable=False)
    importe        = Column(Float,   nullable=False)

    nota     = relationship("NotaVentaORM", back_populates="contenido")
    producto = relationship("ProductoORM")


Base.metadata.create_all(bind=engine)


# ── Helpers de acceso ──────────────────────

def cliente_get(clienteID: str) -> Optional[ClienteORM]:
    with SessionLocal() as s:
        return s.get(ClienteORM, clienteID)


def domicilio_get(domicilioID: str) -> Optional[DomicilioORM]:
    with SessionLocal() as s:
        return s.get(DomicilioORM, domicilioID)


def producto_get(productoID: str) -> Optional[ProductoORM]:
    with SessionLocal() as s:
        return s.get(ProductoORM, productoID)


def nota_insert(nota: NotaVentaORM) -> None:
    with SessionLocal() as s:
        s.add(nota)
        s.commit()


def nota_get(notaVentaID: str) -> Optional[NotaVentaORM]:
    with SessionLocal() as s:
        return s.get(NotaVentaORM, notaVentaID)


def contenido_insert(item: ContenidoNotaORM) -> None:
    with SessionLocal() as s:
        s.add(item)
        s.commit()


def contenido_get_by_nota(notaVentaID: str) -> List[ContenidoNotaORM]:
    with SessionLocal() as s:
        return s.query(ContenidoNotaORM).filter_by(notaVentaID=notaVentaID).all()