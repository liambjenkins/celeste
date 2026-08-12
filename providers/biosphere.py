import earthaccess
import xarray as xr
import numpy as np
def get_biosphere(
    latitude,
    longitude,
    requested_time
):
    import os

    has_credentials = (
        bool(os.getenv("EARTHDATA_TOKEN"))
        or (
            bool(os.getenv("EARTHDATA_USERNAME"))
            and bool(os.getenv("EARTHDATA_PASSWORD"))
        )
    )

    if not has_credentials:
        return {
            "source": "NASA Earthdata",
            "available": False,
            "reason": "Earthdata credentials not configured",
        }

    earthaccess.login(
        strategy="environment"
    )
    # ---------------------------------------------------------
    # NASA / ORNL GIMMS-3G+ AVHRR
    #
    # Historical global vegetation reconstruction
    #
    # Coverage:
    #   1982-2022
    #
    # Temporal:
    #   twice-monthly composites
    #
    # Spatial:
    #   approximately 0.0833 degree
    # ---------------------------------------------------------
    results = earthaccess.search_data(
        concept_id="C2759076389-ORNL_CLOUD",
        temporal=(
            requested_time.strftime(
                "%Y-%m-%dT00:00:00"
            ),
            requested_time.strftime(
                "%Y-%m-%dT23:59:59"
            )
        ),
        bounding_box=(
            longitude - 0.1,
            latitude - 0.1,
            longitude + 0.1,
            latitude + 0.1
        )
    )
    if not results:
        return {
            "source":
                "NASA/ORNL GIMMS-3G+ AVHRR",
            "available":
                False,
            "reason":
                "No GIMMS-3G+ NDVI granule found"
        }
    # ---------------------------------------------------------
    # Download matching granule
    # ---------------------------------------------------------
    files = earthaccess.download(
        results[:1]
    )
    if not files:
        return {
            "source":
                "NASA/ORNL GIMMS-3G+ AVHRR",
            "available":
                False,
            "reason":
                "GIMMS granule could not be downloaded"
        }
    ds = xr.open_dataset(
        files[0]
    )
    try:
        # -----------------------------------------------------
        # Identify latitude / longitude coordinates
        # -----------------------------------------------------
        if "lat" in ds.coords:
            latitude_name = "lat"
        elif "latitude" in ds.coords:
            latitude_name = "latitude"
        else:
            return {
                "source":
                    "NASA/ORNL GIMMS-3G+ AVHRR",
                "available":
                    False,
                "reason":
                    "No latitude coordinate found"
            }
        if "lon" in ds.coords:
            longitude_name = "lon"
        elif "longitude" in ds.coords:
            longitude_name = "longitude"
        else:
            return {
                "source":
                    "NASA/ORNL GIMMS-3G+ AVHRR",
                "available":
                    False,
                "reason":
                    "No longitude coordinate found"
            }
        # -----------------------------------------------------
        # Select nearest grid cell
        # -----------------------------------------------------
        point = ds.sel(
            {
                latitude_name:
                    latitude,
                longitude_name:
                    longitude
            },
            method="nearest"
        )
        # -----------------------------------------------------
        # Time coordinate
        # -----------------------------------------------------
        if "time" not in point.coords:
            return {
                "source":
                    "NASA/ORNL GIMMS-3G+ AVHRR",
                "available":
                    False,
                "reason":
                    "GIMMS dataset has no time coordinate"
            }
        # -----------------------------------------------------
        # FIX:
        #
        # Convert requested Python datetime into NumPy
        # datetime64 so it can safely be compared with the
        # NetCDF time coordinate.
        # -----------------------------------------------------
        requested_timestamp = np.datetime64(
            requested_time
        )
        time_values = np.asarray(
            point["time"].values
        )
        # Convert the time values to datetime64 explicitly.
        #
        # This handles NetCDF/xarray datetime precision
        # consistently.
        # -----------------------------------------------------
        time_values = time_values.astype(
            "datetime64[ns]"
        )
        requested_timestamp = (
            requested_timestamp
            .astype("datetime64[ns]")
        )
        differences = np.abs(
            time_values
            - requested_timestamp
        )
        nearest_index = int(
            np.argmin(
                differences
            )
        )
        point = point.isel(
            time=nearest_index
        )
        # -----------------------------------------------------
        # Find NDVI variable
        # -----------------------------------------------------
        ndvi_name = None
        for name in point.data_vars:
            if name.lower() == "ndvi":
                ndvi_name = name
                break
        if ndvi_name is None:
            return {
                "source":
                    "NASA/ORNL GIMMS-3G+ AVHRR",
                "available":
                    False,
                "reason":
                    "No NDVI variable found in GIMMS granule"
            }
        # -----------------------------------------------------
        # Extract NDVI
        #
        # GIMMS NDVI is scaled by 10,000.
        #
        # Invalid values are <= -5000.
        # -----------------------------------------------------
        try:
            raw_ndvi = float(
                point[ndvi_name].values
            )
        except Exception:
            raw_ndvi = None
        if raw_ndvi is None:
            ndvi = None
        elif raw_ndvi <= -5000:
            ndvi = None
        else:
            ndvi = (
                raw_ndvi / 10000.0
            )
        # -----------------------------------------------------
        # Interpret vegetation signal descriptively.
        #
        # This is NOT a prediction.
        # -----------------------------------------------------
        if ndvi is None:
            vegetation_signal = None
        elif ndvi < 0:
            vegetation_signal = (
                "non-vegetated or water-like signal"
            )
        elif ndvi < 0.2:
            vegetation_signal = (
                "very sparse vegetation"
            )
        elif ndvi < 0.4:
            vegetation_signal = (
                "sparse to moderate vegetation"
            )
        elif ndvi < 0.6:
            vegetation_signal = (
                "moderate vegetation"
            )
        elif ndvi < 0.8:
            vegetation_signal = (
                "dense vegetation"
            )
        else:
            vegetation_signal = (
                "very dense vegetation"
            )
        # -----------------------------------------------------
        # Actual grid location
        # -----------------------------------------------------
        grid_latitude = float(
            point[latitude_name].values
        )
        grid_longitude = float(
            point[longitude_name].values
        )
        # -----------------------------------------------------
        # Actual composite date
        # -----------------------------------------------------
        observed_time = str(
            point["time"].values
        )
        # -----------------------------------------------------
        # Return Celeste biosphere layer
        # -----------------------------------------------------
        return {
            "source":
                "NASA/ORNL GIMMS-3G+ AVHRR",
            "available":
                ndvi is not None,
            "metadata": {
                "dataset":
                    "Global Vegetation Greenness "
                    "(NDVI) from AVHRR GIMMS-3G+",
                "version":
                    "GIMMS-3G+ v1.2",
                "coverage":
                    "1982-2022",
                "spatial_resolution":
                    "0.0833 degree",
                "temporal_resolution":
                    "Twice-monthly composite",
                "description":
                    (
                        "Historical global vegetation "
                        "greenness reconstruction derived "
                        "from calibrated AVHRR observations"
                    )
            },
            "requested_time":
                requested_time.isoformat(),
            "observed_time":
                observed_time,
            "location": {
                "latitude":
                    latitude,
                "longitude":
                    longitude
            },
            "grid_cell": {
                "latitude":
                    grid_latitude,
                "longitude":
                    grid_longitude
            },
            "observations": {
                "vegetation": {
                    "ndvi":
                        ndvi,
                    "signal":
                        vegetation_signal
                }
            }
        }
    finally:
        ds.close()