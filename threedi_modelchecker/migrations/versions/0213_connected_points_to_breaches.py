"""clean unused connected points and transform remaining to potential breaches

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
from sqlalchemy import String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

import logging


# revision identifiers, used by Alembic.
revision = "0213"
down_revision = "0212"
branch_labels = None
depends_on = None

logger = logging.getLogger(__name__)

## Copy of the ORM at this point in time:

Base = declarative_base()


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


class ConnectionNode(Base):
    __tablename__ = "v2_connection_nodes"
    id = Column(Integer, primary_key=True)
    the_geom = Column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=True, management=True),
        nullable=False,
    )


class Manhole(Base):
    __tablename__ = "v2_manhole"

    id = Column(Integer, primary_key=True)
    connection_node_id = Column(
        Integer,
        ForeignKey(ConnectionNode.__tablename__ + ".id"),
        nullable=False,
        unique=True,
    )


class Channel(Base):
    __tablename__ = "v2_channel"

    id = Column(Integer, primary_key=True)
    calculation_type = Column(Integer, nullable=False)
    connection_node_start_id = Column(Integer, nullable=False)
    connection_node_end_id = Column(Integer, nullable=False)


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
        .filter(
            (ConnectedPoint.the_geom != CalculationPoint.the_geom)
            | (ConnectedPoint.exchange_level > -9999.0)
            | (ConnectedPoint.levee_id != None)
        )
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


def get_channel_id(session, user_ref):
    type_ref, pk = parse_connected_point_user_ref(user_ref)
    if type_ref == "v2_channel":
        return pk
    elif type_ref == "v2_manhole":
        return get_channel_id_manhole(session, pk)
    return None


def get_channel_id_manhole(session, pk):
    obj = session.query(Manhole).filter(Manhole.id == pk).first()
    if obj is None:
        return
    connection_node_id = obj.connection_node_id

    # find a channel connected to this connection node, with connected calc type
    channels = (
        session.query(Channel)
        .filter(
            (
                (Channel.connection_node_start_id == connection_node_id)
                | (Channel.connection_node_end_id == connection_node_id)
            )
            & Channel.calculation_type.in_([102, 105])
        )
        .all()
    )

    # prefer double connected, and then prefer lowest id
    channels = sorted(channels, key=lambda x: (-x.calculation_type, x.id))
    return None if len(channels) == 0 else channels[0].id


def get_channel_id_boundary_condition(session, pk):
    return pk


def to_potential_breach(session, conn_point_id):
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
        .one()
    )

    channel_id = get_channel_id(session, calculation_point.user_ref)
    if channel_id is None:
        return

    if connected_point.exchange_level not in (None, -9999.0):
        exchange_level = connected_point.exchange_level
    elif levee is not None:
        exchange_level = levee.crest_level
    else:
        exchange_level = None

    if levee is not None:
        maximum_breach_depth = levee.max_breach_depth
    else:
        maximum_breach_depth = None

    if exchange_level == -9999.0:
        exchange_level = None
    if maximum_breach_depth == -9999.0:
        maximum_breach_depth = None

    return PotentialBreach(
        code="#".join([str(connected_point.id), calculation_point.user_ref])[:100],
        exchange_level=exchange_level,
        maximum_breach_depth=maximum_breach_depth,
        levee_material=levee.material if levee is not None else None,
        the_geom=line_geom,
        channel_id=channel_id,
    )


def upgrade():
    session = Session(bind=op.get_bind())

    conn_point_ids = clean_connected_points(session)
    for conn_point_id in conn_point_ids:
        breach = to_potential_breach(session, conn_point_id)
        if breach is None:
            logger.warning(
                "Connected Point %d will be removed because it "
                "cannot be related to a channel. This may influence the "
                "1D-2D exchange of the model.",
                conn_point_id,
            )
        else:
            session.add(breach)
    session.flush()


def downgrade():
    pass
