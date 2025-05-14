# vaccination_dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="COVID-19 Vaccination Dashboard",
    page_icon="💉",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv("owid-covid-data.csv", parse_dates=['date'])
    df['pct_vaccinated'] = (df['people_vaccinated'] / df['population']) * 100
    df['pct_fully_vaccinated'] = (df['people_fully_vaccinated'] / df['population']) * 100
    return df

df = load_data()

# Sidebar controls
st.sidebar.header("Dashboard Controls")

# Country selection (with continent filtering)
continents = ['All'] + sorted(df['continent'].dropna().unique())
selected_continent = st.sidebar.selectbox("Filter by continent", continents)

# Get available countries based on continent filter
if selected_continent == 'All':
    available_countries = sorted(df['location'].unique())
else:
    available_countries = sorted(df[df['continent'] == selected_continent]['location'].unique())

# Set default countries that exist in available_countries
default_options = ["United States", "United Kingdom", "Germany", "Canada", "Australia"]
safe_defaults = [c for c in default_options if c in available_countries][:3]  # Take first 3 matches

# If still no matches, use first available countries
if not safe_defaults and len(available_countries) > 0:
    safe_defaults = available_countries[:min(3, len(available_countries))]

selected_countries = st.sidebar.multiselect(
    "Select countries",
    options=available_countries,
    default=safe_defaults
)

# Final validation
if not selected_countries:
    st.warning("Please select at least one country")
    st.stop()
# Date range selection
min_date = df['date'].min().to_pydatetime()
max_date = df['date'].max().to_pydatetime()
date_range = st.sidebar.date_input(
    "Select date range",
    value=[min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

# Main dashboard
st.title("🌍 COVID-19 Vaccination Progress Dashboard")
st.markdown("Analyze global vaccination trends using data from Our World in Data")

# Metrics row
if selected_countries and len(date_range) == 2:
    filtered_df = df[
        (df['location'].isin(selected_countries)) & 
        (df['date'].between(pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])))
    ]
    
    latest_data = filtered_df.groupby('location').last().reset_index()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        avg_vax = latest_data['pct_vaccinated'].mean()
        st.metric("Avg. Vaccinated (≥1 dose)", f"{avg_vax:.1f}%")
    with col2:
        avg_fully_vax = latest_data['pct_fully_vaccinated'].mean()
        st.metric("Avg. Fully Vaccinated", f"{avg_fully_vax:.1f}%")
    with col3:
        total_pop = latest_data['population'].sum() / 1e9
        st.metric("Total Population", f"{total_pop:.2f} Billion")

# Visualization tabs
tab1, tab2, tab3 = st.tabs(["📈 Time Series", "📊 Comparisons", "🗺️ Geographic View"])

with tab1:
    st.header("Vaccination Progress Over Time")
    if selected_countries:
        fig = px.line(
            filtered_df,
            x="date",
            y="pct_vaccinated",
            color="location",
            labels={"pct_vaccinated": "% Population Vaccinated"},
            hover_data=["people_vaccinated", "population"],
            title="At Least One Dose"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        fig = px.line(
            filtered_df,
            x="date",
            y="pct_fully_vaccinated",
            color="location",
            labels={"pct_fully_vaccinated": "% Population Fully Vaccinated"},
            hover_data=["people_fully_vaccinated"],
            title="Fully Vaccinated"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Please select at least one country")

with tab2:
    st.header("Comparative Analysis")
    if selected_countries:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Latest Vaccination Rates")
            fig = px.bar(
                latest_data,
                x="location",
                y=["pct_vaccinated", "pct_fully_vaccinated"],
                barmode="group",
                labels={"value": "% Population", "variable": "Vaccination Status"},
                title="Vaccination Percentage Comparison"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Vaccination Status")
            selected_country = st.selectbox("Select country for pie chart", selected_countries)
            country_data = latest_data[latest_data['location'] == selected_country].iloc[0]
            
            vaccinated = country_data['pct_vaccinated']
            fully_vaccinated = country_data['pct_fully_vaccinated']
            unvaccinated = 100 - vaccinated
            
            fig = px.pie(
                values=[fully_vaccinated, vaccinated-fully_vaccinated, unvaccinated],
                names=['Fully Vaccinated', 'Partially Vaccinated', 'Unvaccinated'],
                title=f"Vaccination Status: {selected_country}",
                color_discrete_sequence=px.colors.sequential.YlGn[::-1]  
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Please select at least one country")

with tab3:
    st.header("Global Vaccination View")
    world_data = df[df['date'] == df['date'].max()]
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("At Least One Dose")
        fig = px.choropleth(
            world_data,
            locations="location",
            locationmode="country names",
            color="pct_vaccinated",
            hover_name="location",
            hover_data=["people_vaccinated", "population"],
            color_continuous_scale=px.colors.sequential.YlOrRd,
            range_color=(0, 100),
            title="Global Vaccination Rates (% Population)"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Fully Vaccinated")
        fig = px.choropleth(
            world_data,
            locations="location",
            locationmode="country names",
            color="pct_fully_vaccinated",
            hover_name="location",
            hover_data=["people_fully_vaccinated"],
            color_continuous_scale=px.colors.sequential.YlGn,
            range_color=(0, 100),
            title="Global Full Vaccination Rates (% Population)"
        )
        st.plotly_chart(fig, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("""
**Data Source**: [Our World in Data](https://github.com/owid/covid-19-data)  
**Last Updated**: {date}  
**Dashboard Code**: [GitHub Repository](https://github.com/Jb-rown/covid-vaccination-dashboard)
""".format(date=max_date.strftime("%Y-%m-%d")))

