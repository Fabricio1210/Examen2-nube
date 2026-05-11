from sqlalchemy import create_engine, Column, String, Float, Enum, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from typing import Optional
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

    domicilios = relationship("DomicilioORM", back_populates="cliente")


class DomicilioORM(Base):
    __tablename__ = "Domicilio"

    domicilioID   = Column(String(36),  primary_key=True)
    clienteID     = Column(String(36),  ForeignKey("Cliente.clienteID"), nullable=False)
    domicilio     = Column(String(100), nullable=False)
    colonia       = Column(String(100), nullable=False)
    municipio     = Column(String(100), nullable=False)
    estado        = Column(String(100), nullable=False)
    tipodireccion = Column(Enum("FACTURACION", "ENVIO"), nullable=False)

    cliente = relationship("ClienteORM", back_populates="domicilios")


class ProductoORM(Base):
    __tablename__ = "Producto"

    productoID   = Column(String(36),  primary_key=True)
    nombre       = Column(String(100), nullable=False)
    unidadMedida = Column(String(100), nullable=False)
    precioBase   = Column(Float,       nullable=False)


Base.metadata.create_all(bind=engine)


# ── Clientes ──────────────────────────────

def cliente_insert(cliente: ClienteORM) -> None:
    with SessionLocal() as s:
        s.add(cliente)
        s.commit()


def cliente_get(clienteID: str) -> Optional[ClienteORM]:
    with SessionLocal() as s:
        return s.get(ClienteORM, clienteID)


def cliente_update(clienteID: str, datos: dict) -> None:
    with SessionLocal() as s:
        s.query(ClienteORM).filter_by(clienteID=clienteID).update(datos)
        s.commit()


def cliente_delete(clienteID: str) -> None:
    with SessionLocal() as s:
        obj = s.get(ClienteORM, clienteID)
        s.delete(obj)
        s.commit()


# ── Domicilios ────────────────────────────

def domicilio_insert(domicilio: DomicilioORM) -> None:
    with SessionLocal() as s:
        s.add(domicilio)
        s.commit()


def domicilio_get(domicilioID: str) -> Optional[DomicilioORM]:
    with SessionLocal() as s:
        return s.get(DomicilioORM, domicilioID)


def domicilio_update(domicilioID: str, datos: dict) -> None:
    with SessionLocal() as s:
        s.query(DomicilioORM).filter_by(domicilioID=domicilioID).update(datos)
        s.commit()


def domicilio_delete(domicilioID: str) -> None:
    with SessionLocal() as s:
        obj = s.get(DomicilioORM, domicilioID)
        s.delete(obj)
        s.commit()


# ── Productos ─────────────────────────────

def producto_insert(producto: ProductoORM) -> None:
    with SessionLocal() as s:
        s.add(producto)
        s.commit()


def producto_get(productoID: str) -> Optional[ProductoORM]:
    with SessionLocal() as s:
        return s.get(ProductoORM, productoID)


def producto_update(productoID: str, datos: dict) -> None:
    with SessionLocal() as s:
        s.query(ProductoORM).filter_by(productoID=productoID).update(datos)
        s.commit()


def producto_delete(productoID: str) -> None:
    with SessionLocal() as s:
        obj = s.get(ProductoORM, productoID)
        s.delete(obj)
        s.commit()