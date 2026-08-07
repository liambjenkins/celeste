import requests

from datetime import timedelta, datetime

from utils.geo import haversine_distance_km


def get_earthquakes(
    latitude,
    longitude,
    requested_time
):

    start_time = requested_time - timedelta(hours=24)
    end_time = requested_time + timedelta(hours=24)


    url = "https://earthquake.usgs.gov/fdsnws/event/1/query"


    params = {

        "format": "geojson",

        "starttime": start_time.isoformat(),

        "endtime": end_time.isoformat(),

        "minmagnitude": 3.5,

        "orderby": "time",

        "limit": 100

    }


    response = requests.get(
        url,
        params=params
    )


    data = response.json()


    events = []


    for feature in data.get("features", []):

        properties = feature["properties"]

        coordinates = feature["geometry"]["coordinates"]


        event_lon = coordinates[0]
        event_lat = coordinates[1]
        depth_km = coordinates[2]


        event_time = datetime.fromtimestamp(
            properties["time"] / 1000
        )


        distance_km = haversine_distance_km(
            latitude,
            longitude,
            event_lat,
            event_lon
        )


        time_offset_hours = round(
            (
                event_time - requested_time
            ).total_seconds()
            / 3600,
            2
        )


        events.append({

            "time": event_time.isoformat(),

            "magnitude": properties.get(
                "mag"
            ),

            "location": properties.get(
                "place"
            ),

            "depth_km": depth_km,

            "distance_km": round(
                distance_km,
                2
            ),

            "time_offset_hours": time_offset_hours

        })


    closest_time = sorted(
        events,
        key=lambda x: abs(
            x["time_offset_hours"]
        )
    )[:5]


    closest_distance = sorted(
        events,
        key=lambda x: x["distance_km"]
    )[:5]


    largest = sorted(
        events,
        key=lambda x: x["magnitude"],
        reverse=True
    )[:5]


    return {

        "source": "USGS Earthquake Catalog",

        "requested_time": requested_time.isoformat(),

        "search_window": {

            "before_hours": 24,

            "after_hours": 24

        },

        "minimum_magnitude": 3.5,

        "events_found": len(events),

        "closest_in_time": closest_time,

        "closest_in_distance": closest_distance,

        "largest_events": largest

    }