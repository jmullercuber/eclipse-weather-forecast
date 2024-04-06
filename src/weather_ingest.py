# Go to NOAA website:
#   Find latest forecast
#   for 2024-04-08 18:00 UTC
#   for CONUS region
#   and download it


import json
import os.path
from datetime import datetime, timezone
from ftplib import FTP

SECONDS_PER_HOUR = 3600
ECLIPSE_DATETIME = datetime(year=2024, month=4, day=8, hour=18, tzinfo=timezone.utc)
ALLOWED_FORECAST_HOUR_OFFSET = 6


# Determine latest model
def get_latest_cycle(ftp_client: FTP):
    # Pick latest run date
    blends = ftp_client.nlst()
    latest_blend = sorted(blends)[-1]

    # Pick latest cycle within run date
    cycles = ftp_client.nlst(latest_blend)
    latest_cycle = sorted(cycles)[-1]

    return latest_cycle


def cycle_to_datetime(val: str):
    """Ex. 'blend.20240403/02' --> 2024-04-03T02Z"""
    year, month, day, hour = (
        int(val[6:10]),
        int(val[10:12]),
        int(val[12:14]),
        int(val[15:17]),
    )
    return datetime(year, month, day, hour, tzinfo=timezone.utc)


def hours_until_eclipse(current_dt: datetime, eclipse_dt: datetime):
    diff = eclipse_dt - current_dt
    hours = diff.total_seconds() / SECONDS_PER_HOUR
    return int(hours)


# When far enough in future, the model forecasts for every 3 hours.
# Fallback to closest hour available before the event
def generate_forecast_options(cycle_hour: int, forecast_hour: int):
    results = []
    for hour_offset in range(ALLOWED_FORECAST_HOUR_OFFSET):
        fhour = forecast_hour - hour_offset
        filename = make_forecast_file_name(cycle_hour, forecast_hour)
        results.append((filename, fhour))
    return results


def make_forecast_file_name(cycle_hour: int, forecast_hour: int):
    filename = f"blend.t{cycle_hour:02d}z.core.f{forecast_hour:03d}.co.grib2"
    return filename


def get_forecast(ftp_client: FTP, possible_forecasts: list[tuple[str, int]]):
    available_forecasts = ftp_client.nlst()
    full_path_forecast_options = [
        (fname, fhour)
        for (fname, fhour) in possible_forecasts
        if fname in available_forecasts
    ]

    try:
        return next(iter(full_path_forecast_options))
    except StopIteration:
        raise Exception("no matching forecast found")


def main():
    ftp = FTP("ftp.ncep.noaa.gov")
    ftp.login()
    ftp.cwd("pub/data/nccf/com/blend/prod/")

    latest_cycle = get_latest_cycle(ftp)
    cycle_dt = cycle_to_datetime(latest_cycle)
    forecast_hour = hours_until_eclipse(cycle_dt, ECLIPSE_DATETIME)
    print("Latest Cycle:", latest_cycle)
    print("Forecast hour:", forecast_hour)

    # Search latest cycle for appropriate forecast
    subpath = os.path.join(latest_cycle, "core")
    ftp.cwd(subpath)
    forecast_options = generate_forecast_options(cycle_dt.hour, forecast_hour)
    forecast_name, actual_forecast_hour = get_forecast(ftp, forecast_options)
    print("Found forecast: ", forecast_name)


    # Download forecast
    with open("data/forecast/latest_forecast.grib2", "wb") as f:
        response = ftp.retrbinary("RETR " + forecast_name, f.write)
        print(response)


    # save metadata
    with open("data/forecast/latest_info.json", "w") as f:
        meta = {
            "latest_cycle": latest_cycle,
            "cycle_dt": f"{cycle_dt.replace(tzinfo=None).isoformat()}Z",
            "estimated_forecast_hour": forecast_hour,
            "actual_forecast_hour": actual_forecast_hour,
            "forecast_name": forecast_name,
        }
        json.dump(meta, f, indent=4)

    ftp.close()
    print("Done!")

if __name__=="__main__":
    main()