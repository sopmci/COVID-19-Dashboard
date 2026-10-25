# COVID-19-Dashboard
Interactive COVID-19 dashboard built with Python and Streamlit to explore global and U.S. case and mortality trends through time-series visualizations and interactive geographic maps at the state and county levels.


Live app: paste your Streamlit link here after you deploy

What it does
Line graphs (countries of the world)
Choose a statistic: confirmed cases or deaths
Choose cumulative totals or weekly counts
Pick any date range
Add or remove countries and compare them on one chart
Hover over the lines to see exact values

US map (50 states, DC, and Puerto Rico)

Switch between state-level and county-level maps
Choose confirmed cases or deaths
Choose weekly average or cumulative values for a date range
Places are shaded in green, with darker green meaning higher numbers; hover over a place to see its value
Gray means no data
Data

All COVID-19 numbers come from the Johns Hopkins University Center for Systems Science and Engineering (CSSE) COVID-19 data repository: https://github.com/CSSEGISandData/COVID-19

The data is licensed under CC BY 4.0. If you use it in a publication, the CSSE asks that you cite:

Dong E, Du H, Gardner L. An interactive web-based dashboard to track COVID-19 in real time. Lancet Inf Dis. 20(5):533-534. doi: 10.1016/S1473-3099(20)30120-1

The map also uses two outline files (the shapes of the states and counties):

County outlines from plotly/datasets (MIT license)
State outlines from PublicaMundi/MappingAPI

The data comes straight from those links each time the app starts, so no data files are stored in this repository.

Run it on your own computer
Install Python.
Download this repository (green Code button, then Download ZIP) and unzip it.
Open a terminal in that folder and install what the app needs:
   pip install -r requirements.txt
Start the app:
   streamlit run cap_app.py

It opens in your web browser.

Things to know
The CSSE stopped updating this data on March 9, 2023, so the dashboard ends there.
Weeks run Monday to Sunday and are labeled by their Sunday. The first and last weeks are partial.
Daily numbers sometimes go negative because places correct their earlier counts. Negative weekly values are set to 0 on the map.
Countries that report zero cases in at least 95% of weeks (for example, cruise ships, Antarctica, and North Korea) are removed from the line graphs.
On the map, Puerto Rico is drawn larger and moved next to the mainland so it is easy to see.
The state and county outlines are simplified, so coastlines look a little blocky.
A few places are reported in combined units in the source data (for example, Utah health districts), so they show as gray.
Built with

Streamlit · pandas · Plotly · Folium · streamlit-folium

Author

Your name here
