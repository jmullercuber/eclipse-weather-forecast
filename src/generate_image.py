import json

import geopandas as gpd
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import pandas as pd
import pygrib

###################################
# Load data sources in memory
###################################

def load_forecast():
    with pygrib.open("data/forecast/latest_forecast.grib2") as f:
        tcc = f.select(name="Total Cloud Cover")[0]

    lat,lon = tcc.latlons()

    df = pd.DataFrame(
        {
            "lat": lat.flatten(),
            "lon": lon.flatten(),
            "tcc": tcc.values.flatten(),
        }
    )

    df = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df.lon, df.lat),  # crs="EPSG:4326" # TODO: check CRS
    )

    return df

def load_config():
    try:
        with open("config/config.json", "r") as f:
            config: dict = json.load(f)
            return config
    except (FileNotFoundError, json.JSONDecodeError):
        print("Unable to load config file, using empty dict")
        return {}

def get_points_of_interest(config: dict):
        plot_points_raw = config.get("plot_points", [])

        if plot_points_raw:
            plot_points = gpd.GeoDataFrame(plot_points_raw)
        else:
            print("Did not find points to plot")
            plot_points = gpd.GeoDataFrame(columns=["name", "lon", "lat"])

        plot_points = plot_points.set_geometry(
            gpd.points_from_xy(plot_points["lon"], plot_points["lat"])
        )
        return plot_points

def get_map_bounds(config: dict) -> list[float] | None:
    map_bounds = config.get("map_bounds", {})
    if not map_bounds:
        return None

    lon_bounds = map_bounds.get("longitude")
    lat_bounds = map_bounds.get("latitude")
    assert len(lon_bounds) == 2 and isinstance(lon_bounds, (list, tuple))
    assert len(lat_bounds) == 2 and isinstance(lat_bounds, (list, tuple))

    return [*lon_bounds, *lat_bounds]

def load_base_map():
    NON_CONTINENTAL = ["HI", "VI", "MP", "GU", "AK", "AS", "PR"]
    states = gpd.read_file("data/base_maps/tl_2023_us_state/tl_2023_us_state.shp")
    continental_us: gpd.GeoDataFrame = states[~states["STUSPS"].isin(NON_CONTINENTAL)]
    return continental_us

print("Loading weather...")
df = load_forecast()

print("Loading config...")
CONFIG = load_config()
MAP_BOUNDS = get_map_bounds(CONFIG)
POINTS_OF_INTEREST = get_points_of_interest(CONFIG)

print("Loading base map...")
BASE_MAP = load_base_map()

#####
print("Loading eclipse...")
eclipse_center_path = gpd.read_file(
    "data/eclipse_path/2024eclipse_shapefiles/center.shp"
)
umbra_path = gpd.read_file("data/eclipse_path/2024eclipse_shapefiles/upath_hi.shp")
#####



###################################
# Transformations: Filter/Joining
###################################

#### filter weather data ######
def filter_by_map_region(df: pd.DataFrame, bounds: list[float], buffer: float = 0):
    min_lon, max_lon, min_lat, max_lat = bounds

    return df[
        1
        & (min_lon+buffer < df["lon"])
        & (df["lon"] < max_lon-buffer)
        & (min_lat+buffer < df["lat"])
        & (df["lat"] < max_lat-buffer)
    ]


print("Filtering weather data...")
# TODO: filter by distance to umbra_path

# Restrict to only points visible on map
if MAP_BOUNDS:
    df = filter_by_map_region(df, MAP_BOUNDS, buffer=0.5)

# Arbitrary filter, specified by a query string in config
# My personal config is using simple linear inequalities to limit region
if filter_query := CONFIG.get("filter_query", None):
    df = df.query(filter_query)

# For large regions, pick only a sample of points so plotting is not slow
# df = df.sample(20000)

#### populate points of interest with weather data
print("Finding nearest TCC estimates for Points of Interest...")
POINTS_OF_INTEREST["nearest_tcc"] = POINTS_OF_INTEREST.sjoin_nearest(df)["tcc"]

###################################
# Outputs: Create Plot and Save
###################################

# labels for points of interest
def annotate_row(row: gpd.GeoSeries):
    tcc = row["nearest_tcc"]
    name = row["name"]
    plt.annotate(
        text=f"{name} ({tcc:.0f}%)",
        xy=(row.geometry.x, row.geometry.y),
        xytext=(15, -6),
        textcoords="offset points",
        path_effects=[pe.withStroke(linewidth=4, foreground="w")],
        fontsize=18,
    )

def create_plot(weather_df: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(24, 24))

    BASE_MAP.boundary.plot(color="lightgrey", ax=ax)
    weather_df.plot(
        x="lon", y="lat", kind="scatter", c="tcc", colormap="jet", alpha=0.5, ax=ax
    )
    umbra_path.plot(ax=ax, facecolor="none")
    eclipse_center_path.plot(color="r", ax=ax)
    POINTS_OF_INTEREST.plot(color="r", ax=ax)
    POINTS_OF_INTEREST.apply(annotate_row, axis=1)

    return fig

print("Plotting...")
fig = create_plot(df)
plt.axis(MAP_BOUNDS)
plt.title("Forecasted Total Cloud Cover (%)")
# plt.show()


def get_outfile_name():
    # parse info file
    with open("data/forecast/latest_info.json", "r") as f:
        latest_forcast_info = json.load(f)

    cycle_time = latest_forcast_info["cycle_dt"]
    forecast_hour = latest_forcast_info["actual_forecast_hour"]

    return f"forecast_{cycle_time}_f{forecast_hour}"


fname = get_outfile_name()
out_name = f"data/out/{fname}.png"

print(f"Saving image... {out_name}")
fig.savefig(out_name)


#### all done! ####
print("DONE")