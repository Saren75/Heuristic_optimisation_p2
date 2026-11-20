# OpenSky time-dependent commercial airline graph: 2022-12-01 UTC

This directed multigraph contains observed flights whose first OpenSky message occurred on Thursday, 1 December 2022 UTC. Each edge is one retained flight observation, so the same airport pair and airline can occur many times with different departure and arrival timestamps.

## Files

- opensky_2022-12-01_vertices.csv: 881 airports used by retained edges.
- opensky_2022-12-01_edges.csv: 26,495 observed directed flights.

## Time semantics

departure_time_utc is OpenSky firstseen and arrival_time_utc is OpenSky lastseen. These are the first and last ADS-B messages received for a reconstructed flight, not published schedule times and not guaranteed wheel-off/wheel-on times. All timestamps are ISO 8601 UTC. 3,161 retained flights arrive on 2 December UTC.

A time-dependent path may traverse an edge only when the current arrival time at its origin is no later than departure_time_utc. The next state time becomes arrival_time_utc.

## Selection and enrichment

The December 2022 OpenSky flight list was streamed and filtered to records whose firstseen date is 2022-12-01 UTC. Both endpoints must have an OpenFlights airport record with a valid IATA code and coordinates. To focus on commercial traffic, the first three callsign characters must match an OpenFlights airline ICAO code and that airline record must also have a valid two-character IATA code. Where an ICAO code has more than one airline record, an active record is preferred; the OpenFlights active flag is retained but is known to be imperfect. Exact duplicate source-flight identities are removed. Durations below 15 minutes or above 1,200 minutes are excluded as likely reconstruction artifacts.

The airline assignment is inferred from the callsign prefix. It is not authoritative and does not distinguish marketing from operating carrier in all cases.

## Haversine distance

haversine_km is calculated from the airport coordinates with mean Earth radius 6,371.0088 km. It is a lower bound on flown geographic path length.

## Sources and licence

Flight observations: OpenSky COVID-19 Flight Dataset, December 2022 release, Zenodo record 7923702, DOI 10.5281/zenodo.7923702. The record is marked for non-commercial use; consult the OpenSky terms before redistribution or commercial use.

Airport and airline enrichment: OpenFlights airports.dat and airlines.dat. OpenFlights warns that its static GitHub snapshot and airline active field can be stale.

Source URLs:

- https://opensky-network.org/data/scientific
- https://doi.org/10.5281/zenodo.7923702
- https://openflights.org/data.php

Compressed OpenSky source SHA-256: fccfaee94fc50a5f632245b793192a6f5e44c4aa760b1766c7222c868344cf3b
