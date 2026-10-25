# COVID-19-Dashboard
This COVID-19 Dashboard is an interactive web application developed in Python using Streamlit to explore global and U.S. trends in COVID-19 cases and deaths. The dashboard combines time-series visualizations with geographic maps, allowing users to examine changes over time, compare countries, and explore differences across U.S. states and counties. The dashboard has two tabs: Global Data and U.S. Data. The Global Data tab features interactive line graphs for comparing confirmed COVID-19 cases or deaths across countries over a selected period. The U.S. Data tab displays geographic maps of confirmed cases or deaths at the state or county level. Together, these features provide multiple ways to explore historical COVID-19 trends using publicly available data from the Johns Hopkins University Center for Systems Science and Engineering (JHU CSSE) COVID-19 Data Repository.


**Live app: https://covid-19-dashboard-628.streamlit.app/**

*All COVID-19 numbers come from the Johns Hopkins University Center for Systems Science and Engineering (CSSE) COVID-19 data repository: https://github.com/CSSEGISandData/COVID-19*

The map also uses two outline files (the shapes of the states and counties):
* County outlines from plotly/datasets (MIT license)
* State outlines from PublicaMundi/MappingAPI

Data Cleaning:
* Daily numbers sometimes go negative because places correct their earlier counts. Negative weekly values are set to 0 on the map.
Countries that report zero cases in at least 95% of weeks (for example, cruise ships, Antarctica, and North Korea) are removed from the line graphs.
* On the map, Puerto Rico is drawn larger and moved next to the mainland so it is easy to see.
The state and county outlines are simplified, so coastlines look a little blocky.
* A few places are reported in combined units in the source data (for example, Utah health districts), so they show as gray.


