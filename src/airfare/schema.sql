-- Airfare Price Index schema
-- Normalised: routes and sources are dimensions, fare_observations is the fact table.

CREATE TABLE IF NOT EXISTS routes (
    route_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    origin       CHAR(3) NOT NULL,          -- IATA code, e.g. BOM
    destination  CHAR(3) NOT NULL,          -- IATA code, e.g. DEL
    weight       REAL    NOT NULL DEFAULT 1.0, -- base-period expenditure weight
    UNIQUE (origin, destination)
);

CREATE TABLE IF NOT EXISTS sources (
    source_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL UNIQUE          -- e.g. 'sample', 'airline_x'
);

CREATE TABLE IF NOT EXISTS fare_observations (
    obs_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    route_id      INTEGER NOT NULL REFERENCES routes(route_id),
    source_id     INTEGER NOT NULL REFERENCES sources(source_id),
    collected_on  DATE    NOT NULL,          -- day the price was scraped
    travel_date   DATE    NOT NULL,          -- day of the flight
    days_ahead    INTEGER NOT NULL,          -- booking window (travel_date - collected_on)
    carrier       TEXT    NOT NULL,
    fare_inr      REAL    NOT NULL CHECK (fare_inr > 0),
    UNIQUE (route_id, source_id, collected_on, travel_date, carrier)
);

-- Most index queries filter by collection date and route
CREATE INDEX IF NOT EXISTS idx_obs_date_route
    ON fare_observations (collected_on, route_id);
