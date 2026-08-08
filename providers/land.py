import earthaccess
import xarray as xr
def get_land(
    latitude,
    longitude,
    requested_time
):
    earthaccess.login(
        strategy="environment"
    )
    results = earthaccess.search_data(
        short_name="GLDAS_NOAH025_3H",
        version="2.0",
        temporal=(
            requested_time.strftime("%Y-%m-%d"),
            requested_time.strftime("%Y-%m-%d")
        ),
        bounding_box=(
            longitude - 0.25,
            latitude - 0.25,
            longitude + 0.25,
            latitude + 0.25
        )
    )
    if not results:
        return {
            "source": "NASA GLDAS",
            "available": False,
            "reason": "No GLDAS data found"
        }
    files = earthaccess.download(
        results[:1]
    )
    if not files:
        return {
            "source": "NASA GLDAS",
            "available": False,
            "reason": "GLDAS data could not be downloaded"
        }
    ds = xr.open_dataset(
        files[0]
    )
    try:
        # GLDAS uses a 0.25° grid.
        # Select the grid cell nearest to the requested location.
        #
        # Depending on the file version, coordinates may be named
        # either lat/lon or latitude/longitude.
        if "lat" in ds.coords and "lon" in ds.coords:
            point = ds.sel(
                lat=latitude,
                lon=longitude,
                method="nearest"
            )
        elif "latitude" in ds.coords and "longitude" in ds.coords:
            point = ds.sel(
                latitude=latitude,
                longitude=longitude,
                method="nearest"
            )
        else:
            return {
                "source": "NASA GLDAS",
                "available": False,
                "reason": "GLDAS file has no recognised latitude/longitude coordinates"
            }
        # The downloaded granule is a single 3-hour observation,
        # but retain safe handling in case a time dimension exists.
        if "time" in point.dims:
            point = point.isel(time=0)
        def extract(variable):
            try:
                if variable not in point:
                    return None
                value = point[variable].values
                # Convert numpy scalar values safely.
                value = float(value)
                # GLDAS uses -9999 as a missing-value marker.
                if value <= -9990:
                    return None
                return value
            except Exception:
                return None
        def kelvin_to_celsius(value):
            if value is None:
                return None
            return value - 273.15
        # ---------------------------------------------------------
        # Soil moisture
        # GLDAS units: kg/m²
        # ---------------------------------------------------------
        soil_moisture_0_10 = extract(
            "SoilMoi0_10cm_inst"
        )
        soil_moisture_10_40 = extract(
            "SoilMoi10_40cm_inst"
        )
        soil_moisture_40_100 = extract(
            "SoilMoi40_100cm_inst"
        )
        soil_moisture_100_200 = extract(
            "SoilMoi100_200cm_inst"
        )
        # ---------------------------------------------------------
        # Soil temperature
        # GLDAS units: Kelvin
        # ---------------------------------------------------------
        soil_temp_0_10 = extract(
            "SoilTMP0_10cm_inst"
        )
        soil_temp_10_40 = extract(
            "SoilTMP10_40cm_inst"
        )
        # ---------------------------------------------------------
        # Surface conditions
        # ---------------------------------------------------------
        air_temperature = extract(
            "Tair_f_inst"
        )
        albedo = extract(
            "Albedo_inst"
        )
        evapotranspiration = extract(
            "Evap_tavg"
        )
        # Determine the actual GLDAS grid point used.
        if "lat" in point.coords:
            grid_latitude = float(point["lat"].values)
            grid_longitude = float(point["lon"].values)
        else:
            grid_latitude = float(point["latitude"].values)
            grid_longitude = float(point["longitude"].values)
        return {
            "source": "NASA GLDAS",
            "available": True,
            "metadata": {
                "dataset": "GLDAS NOAH 0.25 degree",
                "description": (
                    "NASA land surface model reconstruction "
                    "of soil moisture, soil temperature and "
                    "surface conditions"
                ),
                "variables": [
                    "soil moisture",
                    "soil temperature",
                    "surface air temperature",
                    "albedo",
                    "evapotranspiration"
                ]
            },
            "requested_time":
                requested_time.isoformat(),
            "location": {
                "latitude": latitude,
                "longitude": longitude
            },
            "grid_cell": {
                "latitude": grid_latitude,
                "longitude": grid_longitude
            },
            "observations": {
                "soil": {
                    "moisture": {
                        "0_10cm_mm":
                            soil_moisture_0_10,
                        "10_40cm_mm":
                            soil_moisture_10_40,
                        "40_100cm_mm":
                            soil_moisture_40_100,
                        "100_200cm_mm":
                            soil_moisture_100_200
                    },
                    "temperature": {
                        "0_10cm_c":
                            kelvin_to_celsius(
                                soil_temp_0_10
                            ),
                        "10_40cm_c":
                            kelvin_to_celsius(
                                soil_temp_10_40
                            )
                    }
                },
                "surface": {
                    "air_temperature_c":
                        kelvin_to_celsius(
                            air_temperature
                        ),
                    "albedo_percent":
                        albedo,
                    "evapotranspiration":
                        evapotranspiration
                }
            }
        }
    finally:
        ds.close()