# 2024 North American Eclipse Forecasting

## Why

To help plan trips to view the eclipse.
Inspired by graphic on New York Times.

Currently hard-coded for values for the 2024 North American Eclipse.

## Getting Started

Assumption is that you have Python and Poetry installed.

```sh
# Install python deps
poetry install
```

Various static data sources also need to be downloaded manually for this program to work.
This is a one-time thing. See [the Manual Resources section](#manual-👷) for more information.

## Usage

Run the following in your terminal:

```sh
./run.sh
```

View the generated image in the `data/out` directory.

Create a [config/config.json](config/config.json) file to adjust program parameters. Refer to the [example config here](config/example_config.json).

## Resources

### Automated 🤖

- ⛅ NOAA National Blend of Models
  - Weather forecast for locations during the eclipse. The total cloud cover metric is the primary data source behind this project, allowing users to understand what sky visibility is expected for a given location. This project focuses on the Contiguous United States (CONUS region). Learn more about the data source here: https://vlab.noaa.gov/web/mdl/nbm-download

### Manual 👷

- 🌑🌞 NASA Scientific Visualization Studio Eclipse Data

  - Path covered by the moon's shadow. Learn more here: https://svs.gsfc.nasa.gov/5073
  - Download `2024eclipse_shapefiles.zip`, and extract to the [data/eclipse_path/](data/eclipse_path/) folder.

- 🗺️ US Census TIGER
  - Base map of United states to help visualize eclipse and weather relative to land. Learn more here: https://www.census.gov/cgi-bin/geo/shapefiles/index.php
  - On the TIGER webpage, select the latest year, and the "States (and equivalent)" Layer type. Submit the form to download. Extract to the [data/base_maps/](data/base_maps/) folder.
