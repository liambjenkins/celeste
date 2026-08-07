import earthaccess
import xarray as xr


def get_biosphere(
    latitude,
    longitude,
    requested_time
):

    earthaccess.login(
        strategy="environment"
    )


    # MODIS vegetation is a 16-day composite,
    # so search a wider window

    results = earthaccess.search_data(
        short_name="MOD13Q1",
        version="6.1",
        temporal=(
            requested_time.strftime("%Y-%m-%d"),
            requested_time.strftime("%Y-%m-%d")
        ),
        bounding_box=(
            longitude - 1,
            latitude - 1,
            longitude + 1,
            latitude + 1
        )
    )


    if not results:

        return {

            "source": "NASA MODIS",

            "available": False,

            "reason": (
                "No MODIS vegetation composite "
                "found for this period"
            )

        }


    files = earthaccess.download(
        results[:1]
    )


    ds = xr.open_dataset(
        files[0]
    )


    def extract(variable):

        try:

            value = float(
                ds[variable]
                .values
            )

            return value


        except Exception:

            return None



    ndvi = extract(
        "NDVI"
    )

    evi = extract(
        "EVI"
    )


    if ndvi is not None:
        ndvi *= 0.0001


    if evi is not None:
        evi *= 0.0001



    return {


        "source": "NASA MODIS",


        "available": True,


        "metadata": {

            "dataset":
                "MOD13Q1 Vegetation Indices",

            "description":
                (
                    "Satellite reconstruction "
                    "of vegetation activity"
                )

        },


        "requested_time":
            requested_time.isoformat(),


        "location": {

            "latitude": latitude,

            "longitude": longitude

        },


        "observations": {

            "vegetation": {

                "ndvi":
                    ndvi,

                "evi":
                    evi

            }

        }

    }