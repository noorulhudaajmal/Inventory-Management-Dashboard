import numpy as np
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from streamlit_gsheets import GSheetsConnection
from streamlit_option_menu import option_menu
from scraper.scrape import scrap_data, get_countries_codes
from scraper.calendar_scraper import get_geopolitical_calendar

from utils import months_list, pre_process_data, filter_data, get_coi, get_inv_sold, get_inv_under_repair, \
    get_inv_picked, get_gatein_aging, get_dwell_time, format_kpi_value, pre_process_trading_data
from plots import get_market_price_map, container_count_plot, available_for_sale_plot, sold_inventory_plot, \
    monthly_sales_plot, sales_cost_breakdown_plot, inventory_plot, inventory_per_depot, shipping_costs_plot, \
    container_prices_plot

st.set_page_config(page_title="Inventory Insights", page_icon="📊", layout="wide")

# Update the GSheets connection
conn = st.connection("gsheets", type=GSheetsConnection)
new_conn = st.connection("pricing_data", type=GSheetsConnection)

API_KEY = st.secrets.news_api_key["key"]
API_ENDPOINT = "https://api.newsfilter.io/search?token={}".format(API_KEY)

# ---------------------------------- Page Styling -------------------------------------

with open("css/style.css") as css:
    st.markdown(f'<style>{css.read()}</style>', unsafe_allow_html=True)

st.markdown("""
<style>
    [data-testid=stSidebar] {
        background-color: #708d81;
    }
    [data-testid=stMetricContainer] {
        background-color: #708d81;
    }
</style>
""", unsafe_allow_html=True)

# ----------------------------------- Data Loading ------------------------------------

with st.sidebar:
    file_upload = st.file_uploader("Upload data file", type=["csv", "xlsx", "xls"], )

df = pd.DataFrame()
df0 = pd.DataFrame()
df_trading = pd.DataFrame()

if file_upload is None:
    # Read data directly from Google Sheets
    df = conn.read(worksheet="Data_Sheet")
    df0 = conn.read(worksheet="Container X")
    df_trading = new_conn.read(worksheet="Trading market price")

else:
    if file_upload.type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
        df = pd.read_excel(file_upload, engine="openpyxl", sheet_name="Data_Sheet")
        df0 = pd.read_excel(file_upload, sheet_name="Container X")
    elif file_upload.type == "application/vnd.ms-excel":  # Check if it's an XLS file
        df = pd.read_excel(file_upload, sheet_name="Data_Sheet")
        df0 = pd.read_excel(file_upload, sheet_name="Container X")
    elif file_upload.type == "text/csv":  # Check if it's a CSV file
        df = pd.read_csv(file_upload, encoding=("UTF-8"))

# ---------------------- Data Pre-processing --------------------------------------
df = pre_process_data(df)

year_list = list(set(df[df["Year"] != 0]["Year"].values))
year_list.sort()

colors = ["#264653", "#2a9d8f", "#e9c46a", "#f4a261", "#e76f51", "#84a59d", "#006d77",
          "#f6bd60", "#90be6d", "#577590", "#e07a5f", "#81b29a", "#f2cc8f", "#0081a7"]
# ---------------------------------------------------------------------------------
menu = option_menu(menu_title=None, options=["Overview", "Sales & Costs",
                                             "Inventory In vs. Out", "Sales' Ports",
                                             "Trading Prices",
                                             "Calendar"], orientation="horizontal")

# --------------------------------- Charts  ---------------------------------------
if menu == "Overview":
    # ------------------------ Filters ------------------------------------------------
    location = st.sidebar.multiselect(label="Location",
                                      options=set(df["Location"].dropna().values),
                                      placeholder="All")
    depot = st.sidebar.multiselect(label="Depot",
                                   options=set(df["Depot"].dropna().values),
                                   placeholder="All")
    year = st.sidebar.selectbox(label="Year", options=year_list, index=2)

    # -------------------- Filtered Data -------------------------------------------
    filtered_df = filter_data(df, location, depot)
    filtered_data = filtered_df.copy()
    filtered_df = filtered_df[filtered_df["Year"] == year]
    prev_year_ind = year_list.index(year) - 1
    filtered_df_prev = filtered_data.copy()
    if prev_year_ind >= 0:
        filtered_df_prev = filtered_df_prev[filtered_df_prev["Year"] == year_list[prev_year_ind]]
    else:
        filtered_df_prev = pd.DataFrame()
    # ------------------------- Main Display ---------------------------------------
    if len(filtered_df) == 0:
        st.title("No Data Record found.")
    # -------------------------- KPIs calculation ----------------------------------
    cost_of_inventory, percentage_change_coi = get_coi(filtered_df, filtered_df_prev)
    inventory_sold, percentage_change_is = get_inv_sold(filtered_df, filtered_df_prev)
    inv_under_repair, percentage_change_ur = get_inv_under_repair(filtered_df, filtered_df_prev)
    inv_picked, percentage_change_ip = get_inv_picked(filtered_df, filtered_df_prev)
    gatein_aging, percentage_change_gia = get_gatein_aging(filtered_df, filtered_df_prev)
    dwell_time, percentage_change_dt = get_dwell_time(filtered_df, filtered_df_prev)

    # -------------------------- KPIs Display ---------------------------------------
    kpi_row = st.columns(6)
    kpi_row[0].metric(label="Cost of Inventory",
                      value=f"{format_kpi_value(cost_of_inventory)}",
                      delta=f"{percentage_change_coi:.1f}%")

    kpi_row[1].metric(label="Inventory Sold",
                      value=f"{format_kpi_value(inventory_sold)}",
                      delta=f"{percentage_change_is:.1f}%")

    kpi_row[2].metric(label="Inventory Undergoing Repairs",
                      value=f"{format_kpi_value(inv_under_repair)}",
                      delta=f"{percentage_change_ur:.1f}%")

    kpi_row[3].metric(label="Inventory Picked Up",
                      value=f"{inv_picked} items",
                      delta=f"{percentage_change_ip:.1f}%")

    kpi_row[4].metric(label="Gate In",  # Aging of Inventory (Gate In to Today)
                      value=f"{gatein_aging:.1f} days",
                      delta=f"{percentage_change_gia:.1f}%")
    try:
        kpi_row[5].metric(label="Gate Out",  # Dwell Time (Gate In to Sell Date)
                          value=f"{int(dwell_time)} days",
                          delta=f"{percentage_change_dt:.1f}%")
    except ValueError:
        kpi_row[5].metric(label="Gate Out",  # Dwell Time (Gate In to Sell Date)
                          value=f"{0} days",
                          delta=f"{percentage_change_dt:.1f}%")

    charts_row = st.columns(2)
    # -------------------------- Depot Activity ---------------------------------------

    depot_activity_data = filtered_df[filtered_df["Status"] == "SELL"]
    depot_activity = depot_activity_data.groupby(['Depot', 'Size'])['Unit #'].nunique().unstack(fill_value=0)

    fig = available_for_sale_plot(depot_activity)
    charts_row[0].plotly_chart(fig, use_container_width=True)
    # -------------------------- Vendor Ratio ---------------------------------------
    depot_activity_data = filtered_df[filtered_df["Status"] == "SOLD"]
    depot_activity = depot_activity_data.groupby(['Depot', 'Size'])['Unit #'].nunique().unstack(fill_value=0)

    fig = sold_inventory_plot(depot_activity)
    charts_row[1].plotly_chart(fig, use_container_width=True)


# ------------------------------ Page 2 -----------------------------------------------
if menu == "Sales & Costs":
    # ------------------------ Filters ------------------------------------------------
    location = st.sidebar.multiselect(label="Location",
                                      options=set(df["Location"].dropna().values),
                                      placeholder="All")
    depot = st.sidebar.multiselect(label="Depot",
                                   options=set(df["Depot"].dropna().values),
                                   placeholder="All")
    year = st.sidebar.selectbox(label="Year", options=year_list, index=2)

    # -------------------- Filtered Data -------------------------------------------
    filtered_data = filter_data(df, location, depot)
    filtered_data = filtered_data[filtered_data["Year"] == year]

    charts_row = st.columns(2)
    # -------------------------- Monthly Sales Scatter Plot ---------------------------
    fig = monthly_sales_plot(filtered_data)
    charts_row[0].plotly_chart(fig, use_container_width=True)

    # -------------------------- Sales vs. Cost Breakdown Bar plot --------------------
    grouped_data = filtered_data.groupby(['Month'])[['Storage Cost', 'Repair Cost', 'Purchase Cost']].sum()
    grouped_data = grouped_data.reindex(months_list, axis=0)

    # Create the stacked bar chart
    fig = sales_cost_breakdown_plot(grouped_data)
    charts_row[1].plotly_chart(fig, use_container_width=True)

# ------------------------------ Page 3 -----------------------------------------------
if menu == "Inventory In vs. Out":
    # ------------------------ Filters ------------------------------------------------
    location = st.sidebar.multiselect(label="Location",
                                      options=set(df["Location"].dropna().values),
                                      placeholder="All")
    year = st.sidebar.selectbox(label="Year", options=year_list, index=2)

    # -------------------- Filtered Data -------------------------------------------
    filtered_data = filter_data(df, location, depot=None)
    filtered_df = filtered_data[filtered_data["Year"] == year]
    filtered_df['Month'] = pd.Categorical(filtered_df['Month'], categories=months_list, ordered=True)

    charts_row = st.columns(2)

    inv_in_out_data = filtered_df.groupby(["Month"])[["Gate In", "Gate Out"]].count().reset_index()
    inv_in_out_data["Gate Out"] = (-1) * inv_in_out_data["Gate Out"]

    fig = inventory_plot(inv_in_out_data)
    charts_row[0].plotly_chart(fig, use_container_width=True)

    # ------------------------------------------------------------------------------------
    inv_in_out_data = filtered_df.groupby(["Depot"])[["Gate In", "Gate Out"]].count().reset_index()
    inv_in_out_data["Gate Out"] = (-1) * inv_in_out_data["Gate Out"]

    fig = inventory_per_depot(inv_in_out_data)
    charts_row[1].plotly_chart(fig, use_container_width=True)
# ------------------------------ Page 4 -----------------------------------------------
if menu == "Sales' Ports":
    data = pd.DataFrame()
    try:
        data = scrap_data(url="https://moverdb.com/container-shipping/united-states")
    except Exception as e:
        st.warning("Error retrieving data!!!")
        st.info(e)

    row_1 = st.columns((1, 4))
    row_1[0].write("# ")
    row_1[0].write("# ")
    size = row_1[0].selectbox("Size", options=["20FT", "40FT"])
    exports = row_1[0].selectbox("Export Size", options=["Large", "Medium", "Small"])

    small = data[data[size] >= 9000]
    medium = data[((data[size] < 9000) & (data[size] >= 5000))]
    large = data[data[size] < 5000]
    df = pd.DataFrame()
    if exports == "Large":
        df = small
    elif exports == "Medium":
        df = medium
    else:
        df = large

    fig = shipping_costs_plot(df, size)
    row_1[1].plotly_chart(fig, use_container_width=True)
    st.write("---")

    if len(df0) != 0:
        df0["WEEK_TO_DISPLAY"] = pd.to_datetime(df0["WEEK_TO_DISPLAY"])

        row_2 = st.columns((1, 4))
        row_2[0].write("# ")
        row_2[0].write("# ")
        container_type = row_2[0].selectbox(label="Container Type",
                                            options=df0["CONTAINER_TYPE"].unique())
        container_condition = row_2[0].selectbox(label="Container Type",
                                                 options=df0["CONTAINER_CONDITION"].unique())
        selected_data = df0[(df0["CONTAINER_TYPE"] == container_type) &
                            (df0["CONTAINER_CONDITION"] == container_condition)]
        df1 = selected_data.groupby(["WEEK_TO_DISPLAY",
                                     "SALES_LOCATION_NAME"])["MEAN_PRICE_PER_CONTAINER"].mean().reset_index()

        fig = container_prices_plot(df1)
        row_2[1].plotly_chart(fig, use_container_width=True)

# ------------------------------ Page 5 -----------------------------------------------
if menu == "Calendar":
    df = get_geopolitical_calendar()

    # Display the DataFrame as a table
    styler = df.style.hide_index()
    st.write(styler.to_html(escape=False), unsafe_allow_html=True)

# -------------------------------------------------------------------------------------------------------

if menu == "Trading Prices":
    st.markdown(
        f"""
    <style>
    .stPlotlyChart {{
     outline: 5px solid {'#FFFFFF'};
     border-radius: 10px;
     box-shadow: 0 4px 8px 0 rgba(0, 0, 0, 0.20), 0 6px 20px 0 rgba(0, 0, 0, 0.30);
    }}
    </style>
    """, unsafe_allow_html=True
    )
    df_trading = pre_process_trading_data(df_trading)

    outer_cols = st.columns((6, 4))
    with outer_cols[0]:
        st.write("###### ")
        filter_row = st.columns((1, 4, 1))
        selected_range = filter_row[1].slider(
            'Select Date Range:',
            min_value=df_trading['DATE'].min().to_pydatetime(),
            max_value=df_trading['DATE'].max().to_pydatetime(),
            value=(df_trading['DATE'].min().to_pydatetime(), df_trading['DATE'].max().to_pydatetime()),
            format='MMM YYYY'
        )
        selected_start, selected_end = pd.to_datetime(selected_range[0]), pd.to_datetime(selected_range[1])
        filtered_df = df_trading[(df_trading['DATE'] >= selected_start) & (df_trading['DATE'] <= selected_end)]

        container_count_fig = container_count_plot(filtered_df)
        st.plotly_chart(container_count_fig, use_container_width=True)

    with outer_cols[1]:
        filter_row = st.columns(3)
        st.write("### ")
        cities = df_trading['CITY'].unique()
        selected_city = filter_row[0].selectbox(label="Location", options=cities)
        filtered_trading_data = df_trading[df_trading['CITY'] == selected_city]

        # temp = filtered_trading_data.groupby(['Month', 'Year'])['MARKET_PRICE_USD'].sum().reset_index()
        # st.dataframe(temp)
        heatmap_fig = get_market_price_map(filtered_trading_data)

        st.plotly_chart(heatmap_fig, use_container_width=True)

# -------------------------------------------------------------------------------------------------------
