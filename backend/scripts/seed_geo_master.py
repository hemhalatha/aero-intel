from geoalchemy2 import WKTElement
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_session_local
from app.geo_master.models import City, LandUseZone, MonitoringStation, RoadSegment, Ward


def polygon(points: list[tuple[float, float]]) -> WKTElement:
    coordinates = ", ".join(f"{longitude} {latitude}" for latitude, longitude in points)
    return WKTElement(f"POLYGON(({coordinates}))", srid=4326)


def line(points: list[tuple[float, float]]) -> WKTElement:
    coordinates = ", ".join(f"{longitude} {latitude}" for latitude, longitude in points)
    return WKTElement(f"LINESTRING({coordinates})", srid=4326)


def point(latitude: float, longitude: float) -> WKTElement:
    return WKTElement(f"POINT({longitude} {latitude})", srid=4326)


def seed(db: Session) -> None:
    city = db.scalar(select(City).where(City.code == "BLR"))
    if city is None:
        city = City(
            code="BLR",
            name="Bengaluru",
            state="Karnataka",
            country="India",
            center_latitude=12.9716,
            center_longitude=77.5946,
        )
        db.add(city)
        db.flush()

    ward_specs = [
        {
            "code": "BLR-W-001",
            "name": "Central Business District",
            "population": 84000,
            "boundary": polygon(
                [
                    (12.9890, 77.5800),
                    (12.9890, 77.6150),
                    (12.9600, 77.6150),
                    (12.9600, 77.5800),
                    (12.9890, 77.5800),
                ]
            ),
        },
        {
            "code": "BLR-W-002",
            "name": "Indiranagar",
            "population": 97000,
            "boundary": polygon(
                [
                    (13.0000, 77.6250),
                    (13.0000, 77.6550),
                    (12.9600, 77.6550),
                    (12.9600, 77.6250),
                    (13.0000, 77.6250),
                ]
            ),
        },
        {
            "code": "BLR-W-003",
            "name": "Peenya Industrial Area",
            "population": 116000,
            "boundary": polygon(
                [
                    (13.0550, 77.4900),
                    (13.0550, 77.5450),
                    (13.0000, 77.5450),
                    (13.0000, 77.4900),
                    (13.0550, 77.4900),
                ]
            ),
        },
    ]

    wards: dict[str, Ward] = {}
    for spec in ward_specs:
        ward = db.scalar(select(Ward).where(Ward.city_id == city.id, Ward.code == spec["code"]))
        if ward is None:
            ward = Ward(city_id=city.id, **spec)
            db.add(ward)
            db.flush()
        wards[ward.code] = ward

    station_specs = [
        ("BLR-CBD-AQ", "CBD Air Quality Station", "BLR-W-001", 12.9758, 77.6068),
        ("BLR-IND-AQ", "Indiranagar 100 Feet Road Station", "BLR-W-002", 12.9784, 77.6408),
        ("BLR-PEE-AQ", "Peenya Industrial Station", "BLR-W-003", 13.0285, 77.5197),
    ]
    for code, name, ward_code, latitude, longitude in station_specs:
        exists = db.scalar(select(MonitoringStation.id).where(MonitoringStation.code == code))
        if exists is None:
            db.add(
                MonitoringStation(
                    city_id=city.id,
                    ward_id=wards[ward_code].id,
                    code=code,
                    name=name,
                    latitude=latitude,
                    longitude=longitude,
                    location=point(latitude, longitude),
                    is_active=True,
                )
            )

    road_specs = [
        ("BLR-R-MG", "M G Road", "BLR-W-001", "arterial", 3200, [(12.9758, 77.6068), (12.9767, 77.6200)]),
        ("BLR-R-100FT", "100 Feet Road", "BLR-W-002", "arterial", 4100, [(12.9700, 77.6400), (12.9900, 77.6408)]),
        ("BLR-R-PIA", "Peenya Industrial Main Road", "BLR-W-003", "industrial", 5200, [(13.0150, 77.5100), (13.0450, 77.5350)]),
    ]
    for code, name, ward_code, road_class, length_meters, points in road_specs:
        exists = db.scalar(select(RoadSegment.id).where(RoadSegment.city_id == city.id, RoadSegment.code == code))
        if exists is None:
            db.add(
                RoadSegment(
                    city_id=city.id,
                    ward_id=wards[ward_code].id,
                    code=code,
                    name=name,
                    road_class=road_class,
                    length_meters=length_meters,
                    geometry=line(points),
                )
            )

    zone_specs = [
        ("BLR-LU-CBD", "CBD Commercial Core", "BLR-W-001", "commercial", ward_specs[0]["boundary"]),
        ("BLR-LU-IND-MIX", "Indiranagar Mixed Use", "BLR-W-002", "mixed_use", ward_specs[1]["boundary"]),
        ("BLR-LU-PEE-IND", "Peenya Manufacturing Cluster", "BLR-W-003", "industrial", ward_specs[2]["boundary"]),
    ]
    for code, name, ward_code, category, boundary in zone_specs:
        exists = db.scalar(select(LandUseZone.id).where(LandUseZone.city_id == city.id, LandUseZone.code == code))
        if exists is None:
            db.add(
                LandUseZone(
                    city_id=city.id,
                    ward_id=wards[ward_code].id,
                    code=code,
                    name=name,
                    category=category,
                    boundary=boundary,
                )
            )

    db.commit()


def main() -> None:
    with get_session_local()() as db:
        seed(db)


if __name__ == "__main__":
    main()
