from sqlalchemy.orm import Session
from typing import Dict
from typing import List
from typing import Union


# Default values
DWF_FACTORS = [
    [0, 0.03],
    [1, 0.015],
    [2, 0.01],
    [3, 0.01],
    [4, 0.005],
    [5, 0.005],
    [6, 0.025],
    [7, 0.080],
    [8, 0.075],
    [9, 0.06],
    [10, 0.055],
    [11, 0.05],
    [12, 0.045],
    [13, 0.04],
    [14, 0.04],
    [15, 0.035],
    [16, 0.035],
    [17, 0.04],
    [18, 0.055],
    [19, 0.08],
    [20, 0.07],
    [21, 0.055],
    [22, 0.045],
    [23, 0.04],
    [24, 0.0],  # Timeseries for laterals should contain 25 values
]


def read_dwf_per_node(session: Session) -> List[Union[int, float]]:
    """Obtains the DWF per connection node per second a 3Di model sqlite-file."""

    # Create empty list that holds total 24h dry weather flow per node
    dwf_per_node_per_second = []

    # Create a table that contains nr_of_inhabitants per connection_node and iterate over it
    for row in session.execute(
        """
        WITH imp_surface_count AS
            ( SELECT impsurf.id, impsurf.dry_weather_flow,
                     impsurf.dry_weather_flow * impsurf.nr_of_inhabitants AS weighted_flow,
                     impsurf.nr_of_inhabitants / COUNT(impmap.impervious_surface_id) AS nr_of_inhabitants
             FROM v2_impervious_surface impsurf, v2_impervious_surface_map impmap
             WHERE impsurf.nr_of_inhabitants IS NOT NULL AND impsurf.nr_of_inhabitants != 0
             AND impsurf.id = impmap.impervious_surface_id GROUP BY impsurf.id),
        inhibs_per_node AS (
            SELECT impmap.impervious_surface_id, impsurfcount.nr_of_inhabitants,
                   impmap.connection_node_id, impsurfcount.dry_weather_flow, impsurfcount.weighted_flow
            FROM imp_surface_count impsurfcount, v2_impervious_surface_map impmap
            WHERE impsurfcount.id = impmap.impervious_surface_id)
        SELECT ipn.connection_node_id, SUM(ipn.nr_of_inhabitants), SUM(ipn.weighted_flow)
        FROM inhibs_per_node ipn GROUP BY ipn.connection_node_id
        """
    ):
        connection_node_id, nr_of_inhabitants_sum, weighted_flow_sum = row
        # DWF per person example: 120 l/inhabitant / 1000 = 0.12 m3/inhabitant
        dwf_per_node = (
            nr_of_inhabitants_sum * (weighted_flow_sum / nr_of_inhabitants_sum) / 1000
        )
        dwf_per_node_per_second.append([connection_node_id, dwf_per_node / 3600])

    return dwf_per_node_per_second


def generate_dwf_laterals(session: Session) -> List[Dict]:
    """Generate dry weather flow laterals from spatialite"""
    dwf_on_each_node = read_dwf_per_node(session)
    dwf_laterals = []

    # Generate lateral for each connection node
    for node_id, flow in dwf_on_each_node:
        values = [[hour * 3600, flow * factor] for hour, factor in DWF_FACTORS]
        dwf_laterals.append(
            dict(
                offset=0,
                values=values,
                units="m3/s",
                connection_node=node_id,
                interpolate=False,
            )
        )

    return dwf_laterals


class DWFCalculator:
    """Calculate dry weather flow (DWF) from sqlite."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self._laterals = None

    @property
    def laterals(self) -> List[Dict]:
        if self._laterals is None:
            self._laterals = generate_dwf_laterals(self.session)

        return self._laterals
