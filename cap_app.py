import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np
import requests as rq
import bs4
from io import StringIO

import datetime
import folium
from streamlit_folium import st_folium

## -----------------------------------------------
## data importing
## -----------------------------------------------

url_confirmed_g = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv"
url_d_g = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv"

df_cg = pd.read_csv(url_confirmed_g)
df_dg = pd.read_csv(url_d_g)

url_confirmed_us = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_US.csv"
url_d_us = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_US.csv"

#df_cus = pd.read_csv(url_confirmed_us)
#df_dus = pd.read_csv(url_d_us)


## -----------------------------------------------
## data cleaning - global
## -----------------------------------------------

# removing unused columns 
df_cg = df_cg.drop(columns=['Lat', 'Long', 'Province/State'])
df_dg = df_dg.drop(columns=['Lat', 'Long', 'Province/State'])

# fixing : one row per country
df_cg = df_cg.groupby("Country/Region", as_index=False).sum()
df_dg = df_dg.groupby("Country/Region", as_index=False).sum()

# creating dfs with daily rather than cumulative data - global
df_cg_daily = df_cg.copy()
date_cols = df_cg.columns[1:]
df_cg_daily[date_cols] = df_cg[date_cols].diff(axis=1)

df_dg_daily = df_dg.copy()
date_cols = df_dg.columns[1:]
df_dg_daily[date_cols] = df_dg[date_cols].diff(axis=1)

# making daily cases to be weekly instead
df_cg_daily = df_cg_daily.set_index('Country/Region').T.set_axis(pd.to_datetime(df_cg_daily.columns[1:], format = '%m/%d/%y')).resample('W').sum().T
df_cg_daily.columns = df_cg_daily.columns.strftime('%m/%d/%y')

df_dg_daily = df_dg_daily.set_index('Country/Region').T.set_axis(pd.to_datetime(df_dg_daily.columns[1:], format = '%m/%d/%y')).resample('W').sum().T
df_dg_daily.columns = df_dg_daily.columns.strftime('%m/%d/%y')

# same layout as the weekly dfs (country as the index)
df_cg = df_cg.set_index('Country/Region')
df_dg = df_dg.set_index('Country/Region')

# identify countries with >=95% zero daily cases

zero_percent = df_cg_daily.eq(0).mean(axis=1) * 100

countries_to_remove = df_cg_daily.index[zero_percent >= 90].tolist()

# Remove these countries from all DataFrames
df_cg = df_cg.loc[~df_cg.index.isin(countries_to_remove)].copy()
df_dg = df_dg.loc[~df_dg.index.isin(countries_to_remove)].copy()
df_cg_daily = df_cg_daily.loc[~df_cg_daily.index.isin(countries_to_remove)].copy()
df_dg_daily = df_dg_daily.loc[~df_dg_daily.index.isin(countries_to_remove)].copy()


## -----------------------------------------------
## map data cleaning
## -----------------------------------------------
 
# done once, then remembered (so it doesn't re-download / recompute on every click)
if "map_data" not in st.session_state:
 
    df_cus = pd.read_csv(url_confirmed_us)
    df_dus = pd.read_csv(url_d_us)
 
    # boundary files: states (incl. DC and PR) and counties (incl. the 78 PR municipios)
    url_states_geo = "https://raw.githubusercontent.com/PublicaMundi/MappingAPI/master/data/geojson/us-states.json"
    url_counties_geo = "https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json"
    states_geo = rq.get(url_states_geo).json()
    counties_geo = rq.get(url_counties_geo).json()
 
    # state fips code (like '01') <-> state name
    state_names = {f['id']: f['properties']['name'] for f in states_geo['features']}
    name_to_fips = {name: fips for fips, name in state_names.items()}
    county_ids = set(f['id'] for f in counties_geo['features'])
 
    map_data = {}
    for stat, raw in [('Confirmed Cases', df_cus), ('Mortality', df_dus)]:
 
        # date columns are the ones with a '/' in the name (the deaths file has an extra Population column)
        us_date_cols = [c for c in raw.columns if '/' in c]
 
        # keep only the 50 states, DC, and PR (drops Guam, cruise ships, etc.)
        raw = raw[raw['Province_State'].isin(name_to_fips.keys())]
 
        # state level: add up every row in the state (this includes the 'Unassigned' rows)
        df_state = raw.groupby('Province_State')[us_date_cols].sum()
        df_state.index = df_state.index.map(name_to_fips)
 
        # county level: only rows with a FIPS code, written as 5 digits ('1001.0' -> '01001')
        df_county = raw.dropna(subset = ['FIPS']).copy()
        df_county['FIPS'] = df_county['FIPS'].astype(int).astype(str).str.zfill(5)
        df_county = df_county.set_index('FIPS')[us_date_cols]
        df_county = df_county[df_county.index.isin(county_ids)]
 
        for level, df_m in [('State', df_state), ('County', df_county)]:
            # cumulative total at the end of each week
            weekly_cum = df_m.T
            weekly_cum.index = pd.to_datetime(weekly_cum.index, format = '%m/%d/%y')
            weekly_cum = weekly_cum.resample('W').last().T
            # new cases/deaths each week (negative correction weeks set to 0)
            weekly_new = weekly_cum.diff(axis=1)
            weekly_new.iloc[:, 0] = weekly_cum.iloc[:, 0]
            weekly_new = weekly_new.clip(lower = 0)
            map_data[(stat, level)] = (weekly_cum, weekly_new)
 
    st.session_state["states_geo"] = states_geo
    st.session_state["counties_geo"] = counties_geo
    st.session_state["state_names"] = state_names
    st.session_state["map_data"] = map_data
 
 
 
## -----------------------------------------------
## dashboard features
## -----------------------------------------------

# =====================================================================
# Part 1: GLOBAL TAB
# =====================================================================

st.title("COVID-19 Dashboard")

global_tab, us_tab = st.tabs(["Global Data", "US Data"])

with global_tab:

    choose_statistic = st.selectbox("Select:", ['Confirmed Cases', 'Mortality'])
    choose_value = st.selectbox("Select:", ['Cumulative', 'Weekly'])

    if choose_statistic == 'Confirmed Cases' and choose_value == 'Cumulative':
        df = df_cg
    elif choose_statistic == 'Mortality' and choose_value == 'Cumulative':
        df = df_dg
    elif choose_statistic == 'Confirmed Cases' and choose_value == 'Weekly':
        df = df_cg_daily
    elif choose_statistic == 'Mortality' and choose_value == 'Weekly':
        df = df_dg_daily
    else: 
        df = df_cg

    df = df.T
    df.index = pd.to_datetime(df.index, format = '%m/%d/%y')
    
    date_first = df.index.min().date()
    date_last = df.index.max().date()

    date_range = st.slider("Select date range", min_value = date_first, max_value = date_last,
                        value = (date_first, date_last))

    countries = st.multiselect("Select countries:", list(df.columns), default = ['US', 'China', 'Brazil'])

    df = df.loc[pd.Timestamp(date_range[0]):pd.Timestamp(date_range[1])]

    if len(countries) == 0:
        st.write(" ")
    else:
        df = df[countries]
        c_fig = px.line(df, labels = {'index': 'Date', 'value': choose_value, 'variable': 'Country'},
                        title = choose_value + " COVID-19 " + ("Cases" if choose_statistic == "Confirmed Cases" else "Mortality"))
        c_fig.update_layout(hovermode = 'x unified')
        st.plotly_chart(c_fig)


# =====================================================================
# Part 2: US TAB
# =====================================================================
 
with us_tab:
 
    st.header("US Map (50 states, DC, and Puerto Rico)")
 
    map_statistic = st.selectbox("Map statistic:", ['Confirmed Cases', 'Mortality'])
    map_level = st.selectbox("Map level:", ['State', 'County'])
    map_value = st.selectbox("Map values:", ['Weekly average', 'Cumulative'])
 
    weekly_cum, weekly_new = st.session_state["map_data"][(map_statistic, map_level)]
    weeks = weekly_cum.columns
 
    # the slider moves one week at a time, so every position lines up with a week
    map_first = weeks.min().date()
    map_last = weeks.max().date()
    map_range = st.slider("Map date range", min_value = map_first, max_value = map_last,
                          value = (map_first, map_last), step = datetime.timedelta(days = 7))
 
    in_range = (weeks >= pd.Timestamp(map_range[0])) & (weeks <= pd.Timestamp(map_range[1]))
 
    if map_value == 'Cumulative':
        # total as of the last week in the range
        values = weekly_cum.loc[:, weeks[in_range][-1]]
        legend_title = "Cumulative " + map_statistic.lower() + " as of " + map_range[1].strftime('%m/%d/%y')
    else:
        # average of the weekly new counts across the range
        values = weekly_new.loc[:, in_range].mean(axis = 1)
        legend_title = "Average weekly new " + map_statistic.lower() + ", " + map_range[0].strftime('%m/%d/%y') + " to " + map_range[1].strftime('%m/%d/%y')
 
    # shades of green: 7 bins with (roughly) the same number of places in each
    greens = ['#edf8e9', '#c7e9c0', '#a1d99b', '#74c476', '#41ab5d', '#238b45', '#005a32']
    edges = np.unique(np.quantile(values.dropna(), np.linspace(0, 1, 8)))
    n_bins = max(len(edges) - 1, 1)
    bin_colors = [greens[i] for i in np.linspace(0, 6, n_bins).round().astype(int)]
 
    if map_level == 'State':
        geo = st.session_state["states_geo"]
    else:
        geo = st.session_state["counties_geo"]
    state_names = st.session_state["state_names"]
 
    # Puerto Rico is drawn larger and moved next to the mainland (an "inset") so it's easy to see
    pr_scale = 3                    # how many times bigger to draw it (try 2 or 4)
    pr_old_center = (18.22, -66.45) # (lat, lon) where Puerto Rico really is
    pr_new_center = (27.5, -70.0)   # (lat, lon) where it is drawn (ocean southeast of Florida)
 
    def move_pr(coords):
        # works through the nested lists of coordinates in a shape
        if isinstance(coords[0], (int, float)):
            lat_fix = np.cos(np.radians(pr_new_center[0])) / np.cos(np.radians(pr_old_center[0]))
            new_lon = pr_new_center[1] + (coords[0] - pr_old_center[1]) * pr_scale
            new_lat = pr_new_center[0] + (coords[1] - pr_old_center[0]) * pr_scale * lat_fix
            return [new_lon, new_lat]
        return [move_pr(c) for c in coords]
 
    # put the value, color and hover text into each shape
    features = []
    for f in geo['features']:
        geometry = f['geometry']
        if f['id'].startswith('72'):
            geometry = {'type': f['geometry']['type'], 'coordinates': move_pr(f['geometry']['coordinates'])}
        v = values.get(f['id'], np.nan)
        if map_level == 'State':
            label = f['properties']['name']
        else:
            label = f['properties']['NAME'] + " " + f['properties']['LSAD'] + ", " + state_names.get(f['properties']['STATE'], '')
        if pd.isna(v):
            color = '#d3d3d3'
            value_text = "No data"
        else:
            bin_number = min(max(np.searchsorted(edges, v, side = 'right') - 1, 0), n_bins - 1)
            color = bin_colors[bin_number]
            value_text = f"{v:,.1f}" if map_value == 'Weekly average' else f"{v:,.0f}"
        features.append({'type': 'Feature', 'id': f['id'], 'geometry': geometry,
                         'properties': {'label': label, 'value_text': value_text, 'color': color}})
 
    # tiles = None means no background map
    m = folium.Map(location = [39, -98], zoom_start = 3, tiles = None)
    m.get_root().html.add_child(folium.Element("<style>.leaflet-container {background: #f4f4f4;}</style>"))
    folium.GeoJson(
        {'type': 'FeatureCollection', 'features': features},
        style_function = lambda x: {'fillColor': x['properties']['color'],
                                    'color': 'black' if map_level == 'State' else 'white',
                                    'weight': 0.8 if map_level == 'State' else 0.3, 'fillOpacity': 0.9},
        highlight_function = lambda x: {'weight': 2, 'color': 'black'},
        tooltip = folium.GeoJsonTooltip(fields = ['label', 'value_text'], aliases = ['Place:', 'Value:'])
    ).add_to(m)
 
    # county view: also draw a thin black outline around every state / territory (on top of the counties)
    if map_level == 'County':
        state_outlines = []
        for f in st.session_state["states_geo"]['features']:
            geometry = f['geometry']
            if f['id'] == '72':
                geometry = {'type': f['geometry']['type'], 'coordinates': move_pr(f['geometry']['coordinates'])}
            state_outlines.append({'type': 'Feature', 'geometry': geometry, 'properties': {}})
        folium.GeoJson(
            {'type': 'FeatureCollection', 'features': state_outlines},
            style_function = lambda x: {'fill': False, 'color': 'black', 'weight': 0.8},
            interactive = False
        ).add_to(m)
 
    # legend: one colored box per shade with its range, plus gray for no data
    if edges[-1] >= 100:
        fmt = "{:,.0f}"
    else:
        fmt = "{:,.1f}"
    legend_rows = ""
    for i in range(n_bins):
        low = fmt.format(edges[i])
        high = fmt.format(edges[min(i + 1, len(edges) - 1)])
        legend_rows += ("<div><span style='background:" + bin_colors[i] + ";width:16px;height:12px;display:inline-block;margin-right:6px;'></span>"
                        + low + " &ndash; " + high + "</div>")
    legend_rows += "<div><span style='background:#d3d3d3;width:16px;height:12px;display:inline-block;margin-right:6px;'></span>No data</div>"
    legend_html = ("<div style='position:fixed;bottom:20px;left:20px;z-index:9999;background:white;padding:8px 10px;"
                   "border:1px solid #bbb;border-radius:4px;font-size:12px;max-width:260px;'>"
                   "<b>" + legend_title + "</b>" + legend_rows + "</div>")
    m.get_root().html.add_child(folium.Element(legend_html))
 
    # start zoomed to the continental US (Puerto Rico's inset sits inside this view).
    # A tab that isn't showing yet gives the map no size, so fit_bounds alone fails on first load.
    # This re-fits the map as soon as it has a real size (when the tab is opened or the window resizes).
    fit_script = """
    window.addEventListener('load', function() {
        var us_map = MAP_NAME;
        var fit_us = function() {
            us_map.invalidateSize();
            us_map.fitBounds([[24.0, -125.5], [49.8, -66.0]]);
        };
        fit_us();
        new ResizeObserver(fit_us).observe(us_map.getContainer());
    });
    """.replace("MAP_NAME", m.get_name())
    m.get_root().script.add_child(folium.Element(fit_script))
 
    st_folium(m, height = 550, use_container_width = True, returned_objects = [], key = "map_" + map_level)
    st.caption("Puerto Rico is shown enlarged and moved next to the mainland so it is easy to see. "
               "Gray = no data (a few places are reported in combined units, like Utah health districts and Dukes & Nantucket). "
               "Negative weekly corrections are set to 0.")
 