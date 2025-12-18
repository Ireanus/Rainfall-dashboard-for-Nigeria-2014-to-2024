import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
import leafmap.foliumap as leafmap
import plotly.graph_objects as go
import matplotlib.cm as cm
import matplotlib.colors as mcolors

# ---------------------------
# Load data
# ---------------------------
@st.cache_data
def load_data():
    return gpd.read_file("Annual Precipitation_2014_to_2024.geojson")

gdf = load_data()

# ---------------------------
# Streamlit page setup
# ---------------------------
st.set_page_config(layout="wide", page_title="A Dashboard of Rainfall patterns in Nigeria", page_icon="🌍")
st.title("Nigeria's Rainfall Dashboard (2014 - 2024)")

# ---------------------------
# Reshape for line chart
# ---------------------------
df_new = gdf.melt(
    id_vars=["State"], 
    value_vars=[f"{year}_mean" for year in range(2014, 2025)], 
    var_name="Year", 
    value_name="Rainfall (mm)"
)
df_new["Year"] = df_new["Year"].str.replace("_mean", "").astype(int)

# Unique years and states for selectors
years = sorted(df_new["Year"].unique())
states = sorted(df_new["State"].unique())

# Layout
col_side, col_map, col_chart = st.columns([0.7, 3, 1.3])

# shared year selector above the map and tables
with col_map:
    st.markdown("**Use the dropdown below to select the year for the map and tables.**")
    year_selected = st.selectbox("Select Year", years, index=len(years)-1)


# Filter for year
year_data = df_new[df_new['Year'] == year_selected].copy()


# ---------------------------
# TOP CENTER: Choropleth Map
# ---------------------------
with col_map:
    column_name = f"{year_selected}_mean"
    gdf['Rainfall (mm)'] = gdf[column_name].astype(float)

    m = leafmap.Map(center=[9.082, 8.6753], zoom=6.5, tiles="CartoDB.Positron")

    m.add_data(
        gdf,
        column=column_name,
        scheme="NaturalBreaks",   # ✅ classification
        k=5,                      # 5 classes
        cmap="Blues",             # blue gradient for precipitation
        legend_title=f"Rainfall (mm) {year_selected}",
        layer_name=f"Rainfall {year_selected}",
        popups=["State", "Rainfall (mm)"],
        
    )

    m.to_streamlit(height=450)


# -----------Side Data on Highest and Lowest States Precipitation-------------
top3 = year_data.nlargest(3, 'Rainfall (mm)')[['State', 'Rainfall (mm)']].reset_index(drop=True)
low3 = year_data.nsmallest(3, 'Rainfall (mm)')[['State', 'Rainfall (mm)']].reset_index(drop=True)
with col_side:
    st.markdown("Top 3")
    if not top3.empty:
        st.table(top3.set_index("State"))
    else:
        st.write("No data")

    st.markdown("Bottom 3")
    if not low3.empty:
        st.table(low3.set_index("State"))
    else:
        st.write("No data")
    

    # ---- National average for Donut Chart----
    national_avg = year_data["Rainfall (mm)"].mean().round(3)

    # Scale the value between min and max for color mapping
    vmin, vmax = year_data["Rainfall (mm)"].min(), year_data["Rainfall (mm)"].max()
    norm = mcolors.Normalize(vmin=vmin, vmax=vmax)
    cmap = cm.get_cmap("Blues")  # same as map
    color = mcolors.to_hex(cmap(norm(national_avg)))

    # Create donut chart with value in the middle
    fig_donut = go.Figure(data=[go.Pie(
        values=[1],  # single slice
        hole=0.65,  # donut hole size
        marker_colors=[color], # color based on average
        textinfo="none", # no text on slices
        textposition="inside"
    )])

    # Add annotation (value in center)
    fig_donut.update_layout(
        annotations=[
            dict(
                text=f"<b>{national_avg} mm </b>",
                x=0.5, y=0.5, font_size=16, showarrow=False,
                font=dict(color="blue" if norm(national_avg) > 0.5 else "black")
            )
        ],
        showlegend=False,
        margin=dict(t=0, b=0, l=0, r=0),
        height=150,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )

    # Show donut chart
    st.plotly_chart(fig_donut, use_container_width=True)

    # Subtitle below the donut
    st.markdown(
        f"<p style='text-align:center; font-size:14px; color:lightgray;'>"
        f"Nigeria's Average Rainfall Level in <b>{year_selected}</b>"
        f"</p>",
        unsafe_allow_html=True
    )
        

# line chart
with col_chart:
    state_selected = st.selectbox("Select a State to analyze its Rainfall analytics", states, key="state_chart", index=0)
    state_data = df_new[df_new['State'] == state_selected].sort_values('Year')
    fig = px.line(state_data, x='Year', y='Rainfall (mm)', markers=True, labels={"Rainfall (mm)": "Rainfall (mm)", "Year": "Year"})
    fig.update_traces(mode='markers+lines', line=dict(color='blue'))
    st.plotly_chart(fig, use_container_width=True)


# Define the modal function
@st.dialog("Dashboard Information")
def show_info_modal():
    st.markdown("### 🌍 About This Dashboard")
    st.write(
        "This dashboard provides an **interactive visualization of Rainfall "
        "patterns across Nigeria between 2014 and 2024**. "
        "The data was derived and processed in Google Earth Engine, then aggregated per state using Excel & QGIS. "
        "It shows spatial and temporal rainfall analytics accross the country, with the aim of promoting **water accountability**, "
        "and **sustainable water resource management** in each region."
    )

    st.write(
        "Key features include:\n"
        "- Interactive map visualization\n"
        "- Top and bottom 3 states in terms of rainfall volume for each year\n"
        "- Line chart showing annual rainfall analytics per state\n"
        "- Average National rainfall displayed in a donut chart"
    )

    st.markdown("### 👤 Author")
    st.write(
        "This dashboard was created by **Ihomon Msugh-Aondo**, a Geoscientist & Geospatial Analyst, "
        "with experience in **data analysis and visualization**. I love applying innovative methods "
        "and technologies to address water and environmental issues, while promoting **sustainable management practices** "
        "using GIS tools and remote sensing."
    )


    # Add a unique key for the button
    if st.button("OK", key="modal_ok_btn"):
        st.session_state.show_info = False
        st.rerun()


# Check session state to show modal on first load
if "show_info" not in st.session_state:
    st.session_state.show_info = True

if st.session_state.show_info:
    show_info_modal()
else:
    with st.sidebar:
        if st.button("View Info", key="sidebar_info_btn"):
            show_info_modal()