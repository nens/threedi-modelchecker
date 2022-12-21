"""breach and exchange

Revision ID: 0213
Revises: 0212
Create Date: 2022-12-21 14:54:00

"""
from alembic import op
from geoalchemy2.types import Geometry
from sqlalchemy import Column
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import func
from sqlalchemy import Integer
from sqlalchemy import orm
from sqlalchemy import String


# revision identifiers, used by Alembic.
revision = "0213"
down_revision = "0212"
branch_labels = None
depends_on = None


## Copy of the ORM at this point in time:

Base = orm.declarative_base()


class Levee(Base):
    __tablename__ = "v2_levee"
    id = Column(Integer, primary_key=True)
    code = Column(String(100))
    crest_level = Column(Float)
    the_geom = Column(
        Geometry(
            geometry_type="LINESTRING", srid=4326, spatial_index=True, management=True
        ),
        nullable=False,
    )
    material = Column(Integer)
    max_breach_depth = Column(Float)


class CalculationPoint(Base):
    __tablename__ = "v2_calculation_point"
    id = Column(Integer, primary_key=True)

    content_type_id = Column(Integer)
    user_ref = Column(String(80), nullable=False)
    calc_type = Column(Integer)
    the_geom = Column(
        Geometry(geometry_type="POINT", srid=4326),
        nullable=False,
    )


class ConnectedPoint(Base):
    __tablename__ = "v2_connected_pnt"
    id = Column(Integer, primary_key=True)

    calculation_pnt_id = Column(
        Integer, ForeignKey(CalculationPoint.__tablename__ + ".id"), nullable=False
    )
    levee_id = Column(Integer, ForeignKey(Levee.__tablename__ + ".id"))

    exchange_level = Column(Float)
    the_geom = Column(
        Geometry(geometry_type="POINT", srid=4326),
        nullable=False,
    )


class PotentialBreach(Base):
    __tablename__ = "v2_potential_breach"
    id = Column(Integer, primary_key=True)
    code = Column(String(100))
    display_name = Column(String(255))
    exchange_level = Column(Float)
    maximum_breach_depth = Column(Float)
    levee_material = Column(Integer)
    the_geom = Column(
        Geometry(geometry_type="LINESTRING", srid=4326),
        nullable=False,
    )
    channel_id = Column(Integer, nullable=False)


def parse_connected_point_user_ref(user_ref: str):
    """Return content_type, content_id, node_number from a user_ref.

    Raises Exception for various parse errors.

    Example
    -------
    >>> parse_connected_point_user_ref("201#123#v2_channels#4)
    ContentType.TYPE_V2_CHANNEL, 123, 4
    """
    _, id_str, type_str, _ = user_ref.split("#")
    return type_str, int(id_str)


def clean_connected_points(session):
    conn_point_ids = [
        x[0]
        for x in session.query(ConnectedPoint.id)
        .join(CalculationPoint, isouter=True)
        .filter(ConnectedPoint.the_geom != CalculationPoint.the_geom)
        .all()
    ]
    session.query(ConnectedPoint).filter(
        ConnectedPoint.id.notin_(conn_point_ids)
    ).delete(synchronize_session="fetch")
    calc_point_ids = [
        x[0]
        for x in session.query(ConnectedPoint.calculation_pnt_id)
        .filter(ConnectedPoint.id.in_(conn_point_ids))
        .all()
    ]
    session.query(CalculationPoint).filter(
        CalculationPoint.id.notin_(calc_point_ids)
    ).delete(synchronize_session="fetch")
    return conn_point_ids


def transform(session, conn_point_id):
    connected_point, calculation_point, levee, line_geom = (
        session.query(
            ConnectedPoint,
            CalculationPoint,
            Levee,
            func.AsEWKT(
                func.MakeLine(CalculationPoint.the_geom, ConnectedPoint.the_geom)
            ),
        )
        .join(CalculationPoint)
        .join(Levee, isouter=True)
        .filter(ConnectedPoint.id == conn_point_id)
        .first()
    )

    try:
        type_ref, pk = parse_connected_point_user_ref(calculation_point.user_ref)
    except Exception:
        return

    if connected_point.exchange_level is not None:
        exchange_level = connected_point.exchange_level
    elif levee is not None:
        exchange_level = levee.crest_level
    else:
        exchange_level = None

    if type_ref == "v2_channel":
        channel_id = pk
    else:
        raise NotImplementedError()
    return PotentialBreach(
        id=connected_point.id,
        exchange_level=exchange_level,
        maximum_breach_depth=levee.max_breach_depth if levee is not None else None,
        levee_material=levee.material if levee is not None else None,
        the_geom=line_geom,
        channel_id=channel_id,
    )


def upgrade():
    session = orm.Session(bind=op.get_bind())

    clean_connected_points(session)


def downgrade():
    pass
