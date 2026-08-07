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


    ds = xr.open_dataset(
        files[0]
    )


    def extract(variable):

        try:
            return float(
                ds[variable]
                .isel(time=0)
                .values
            )

        except Exception:
            return None


    def kelvin_to_celsius(value):

        if value is None:
            return None

        return value - 273.15


    # Extract once
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

    soil_temp_0_10 = extract(
        "SoilTMP0_10cm_inst"
    )

    soil_temp_10_40 = extract(
        "SoilTMP10_40cm_inst"
    )

    air_temperature = extract(
        "Tair_f_inst"
    )

    albedo = extract(
        "Albedo_inst"
    )

    evapotranspiration = extract(
        "Evap_tavg"
    )


    return {

        "source": "NASA GLDAS",

        "available": True,

        "metadata": {

            "dataset": "GLDAS NOAH 0.25 degree",

            "description": (
                "NASA land surface model reconstruction "
                "of soil, moisture and surface conditions"
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