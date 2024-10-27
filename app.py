import numpy as np
import pandas as pd
import requests
import streamlit as st
import yfinance as yf

from streamlit_gsheets import GSheetsConnection
from streamlit_option_menu import option_menu

from scraper.news_scraper import extract_news
from scraper.scrape import scrap_data
from scraper.calendar_scraper import get_geopolitical_calendar

from utils import months_list, pre_process_data, filter_data, get_coi, get_inv_sold, get_inv_under_repair, \
    get_inv_picked, get_gatein_aging, get_dwell_time, format_kpi_value, pre_process_trading_data, \
    display_telegram_posts, get_commodities_data
from plots import get_market_price_map, container_count_plot, available_for_sale_plot, sold_inventory_plot, \
    monthly_sales_plot, sales_cost_breakdown_plot, inventory_plot, inventory_per_depot, shipping_costs_plot, \
    container_prices_plot, inventory_avb_breakdown_plot, container_prices_wrt_location, \
    biggest_growth_and_drop_in_prices, prices_variation_chart

from const import Commodities

st.set_page_config(page_title="Inventory Insights", page_icon="📊", layout="wide")

# Update the GSheets connection
conn = st.connection("gsheets", type=GSheetsConnection)
new_conn = st.connection("pricing_data", type=GSheetsConnection)

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
    .stMetric {
       background-color: #cce3de;
       # border: 1px solid rgba(28, 131, 225, 0.5);
       padding: 5% 5% 5% 10%;
       border-radius: 10px;
       color: rgb(30, 103, 119);
       overflow-wrap: break-word;
       # height: 120px;
    }
</style>
""", unsafe_allow_html=True)

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

# ----------------------------------- Data Loading ------------------------------------

with st.sidebar:
    file_upload = st.file_uploader("Upload data file", type=["csv", "xlsx", "xls"], )

df = pd.DataFrame()
df_trading = pd.DataFrame()

if file_upload is None:
    # Read data directly from Google Sheets
    df = conn.read(worksheet="Data_Sheet")
    df_trading = new_conn.read(worksheet="Trading market price")

else:
    if file_upload.type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
        df = pd.read_excel(file_upload, engine="openpyxl", sheet_name="Data_Sheet")
    elif file_upload.type == "application/vnd.ms-excel":  # Check if it's an XLS file
        df = pd.read_excel(file_upload, sheet_name="Data_Sheet")
    elif file_upload.type == "text/csv":  # Check if it's a CSV file
        df = pd.read_csv(file_upload, encoding=("UTF-8"))

# ---------------------- Data Pre-processing --------------------------------------
df = pre_process_data(df)
df_trading = pre_process_trading_data(df_trading)

year_list = list(set(df[df["Year"] != 0]["Year"].values))
year_list.sort()

colors = ["#264653", "#2a9d8f", "#e9c46a", "#f4a261", "#e76f51", "#84a59d", "#006d77",
          "#f6bd60", "#90be6d", "#577590", "#e07a5f", "#81b29a", "#f2cc8f", "#0081a7"]
# ---------------------------------------------------------------------------------
menu = option_menu(menu_title=None, options=["Overview", "Sales & Costs",
                                             "Inventory In/Out", "Sales' Ports",
                                             "Trading Prices", "Commodities",
                                             "Calendar", "News"], orientation="horizontal")

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
    # st.write("# ")
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

    # st.write("# ")
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

    st.write("# ")
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
if menu == "Inventory In/Out":
    # st.write("# ")
    inventory_kpis = st.columns(5)

    avb_inv = len(df[df['Status'] == 'SELL'])
    sold_inv = len(df[df['Status'] == 'SOLD'])
    total_gate_in = df["Gate In"].count()
    total_gate_out = df["Gate Out"].count()
    gate_out_in_ratio = total_gate_out / total_gate_in if total_gate_in > 0 else 0

    inventory_kpis[0].metric(label='Available Inventory', value=f'{avb_inv} units')
    inventory_kpis[1].metric(label='Sold Inventory', value=f'{sold_inv} units')
    inventory_kpis[2].metric(label='Total Gate-In', value=f'{total_gate_in} items')
    inventory_kpis[3].metric(label='Total Gate-Out', value=f'{total_gate_out} items')
    inventory_kpis[4].metric(label='Inventory Turnover Ratio', value=f"{gate_out_in_ratio * 100:.1f}%")

    # ------------------------ Filters ------------------------------------------------
    location = st.sidebar.multiselect(label="Location",
                                      options=set(df["Location"].dropna().values),
                                      placeholder="All")
    year = st.sidebar.selectbox(label="Year", options=year_list, index=2)

    # -------------------- Filtered Data -------------------------------------------
    filtered_data = filter_data(df, location, depot=None)
    filtered_df = filtered_data[filtered_data["Year"] == year]
    filtered_df['Month'] = pd.Categorical(filtered_df['Month'], categories=months_list, ordered=True)

    # st.write("# ")
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

    # ---------------------------- Inventory Available for Sale ---------------------------
    st.write("# ")
    row_2 = st.columns((1, 4, 1))
    avb_inventory = df[df['Status'] == 'SELL']
    fig = inventory_avb_breakdown_plot(avb_inventory)

    row_2[1].plotly_chart(fig, use_container_width=True)

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

    st.write("# ")
    fig = shipping_costs_plot(df, size)
    row_1[1].plotly_chart(fig, use_container_width=True)
    st.write("---")

# ------------------------------ Page 5 -----------------------------------------------

if menu == "Trading Prices":
    row_1 = st.columns((1, 1, 1, 2, 1))
    container_type = row_1[1].selectbox(label="Container Type",
                                        options=df_trading["CONTAINER_TYPE"].unique())
    container_condition = row_1[2].selectbox(label="Container Condition",
                                             options=df_trading["CONTAINER_CONDITION"].unique())
    selected_range = row_1[3].slider(
        'Select Date Range:',
        min_value=df_trading['DATE'].min().to_pydatetime(),
        max_value=df_trading['DATE'].max().to_pydatetime(),
        value=(df_trading['DATE'].min().to_pydatetime(), df_trading['DATE'].max().to_pydatetime()),
        format='MMM YYYY'
    )
    selected_start, selected_end = pd.to_datetime(selected_range[0]), pd.to_datetime(selected_range[1])

    # Combine all conditions into a single filter
    filter_mask = ((df_trading['DATE'] >= selected_start) & (df_trading['DATE'] <= selected_end) &
                   (df_trading["CONTAINER_TYPE"] == container_type) &
                   (df_trading["CONTAINER_CONDITION"] == container_condition))
    # Apply the combined filter to df_trading
    filtered_data = df_trading[filter_mask]

    row_2 = st.columns(2)
    row_2[0].plotly_chart(container_prices_wrt_location(filtered_data), use_container_width=True)

    container_count_fig = container_count_plot(filtered_data)
    row_2[1].plotly_chart(container_count_fig, use_container_width=True)

    st.write("# ")

    row_3 = st.columns(2)
    selected_city = row_3[0].selectbox(label="Location", options=filtered_data['CITY'].unique())
    filtered_loc_data = filtered_data[filtered_data['CITY'] == selected_city]
    row_3[0].plotly_chart(container_prices_plot(filtered_loc_data), use_container_width=True)
    row_3[1].write("## ")
    row_3[1].plotly_chart(get_market_price_map(filtered_loc_data), use_container_width=True)

    st.write("# ")
    row_4 = st.columns(2)
    biggest_growth, biggest_drop = biggest_growth_and_drop_in_prices(filtered_data)
    with row_4[0]:
        st.write("##### Locations with biggest Week-on-Week growth")
        # Display the DataFrame as a table
        styler = biggest_growth.head(5).style.applymap(lambda x: 'color:green;' if "%" in x else '').hide()
        st.write(styler.to_html(escape=False), unsafe_allow_html=True)
    with row_4[1]:
        st.write("##### Locations with biggest Week-on-Week drop")
        # Display the DataFrame as a table
        styler = biggest_drop.head(5).style.applymap(lambda x: 'color:red;' if "%" in x else '').hide()
        st.write(styler.to_html(escape=False), unsafe_allow_html=True)

    # table_row[0].plotly_chart(prices_variation_chart(data=biggest_growth.head(5),
    #                                                  indicator='green',
    #                                                  table_title='Locations with biggest Week-on-Week growth'))
    # table_row[1].plotly_chart(prices_variation_chart(data=biggest_drop.head(5),
    #                                                  indicator='red',
    #                                                  table_title='Locations with biggest Week-on-Week drop'))

# -------------------------------------------------------------------------------------------------------

if menu == "Commodities":
    for i in Commodities:
        st.write(f"### {i.name} Commodities Data")
        with st.spinner('Fetching data...'):
            df = get_commodities_data(i.name, i.value)

        col_config = {
            "Trend": st.column_config.AreaChartColumn(
                "Closing Trend",
                width="medium",
                help="The Closing trend for a month",
            ),
        }

        # Function to apply color to cells
        st.data_editor(
            df,
            column_config=col_config,
            hide_index=True,
            use_container_width=True
        )


if menu == "Calendar":
    df = get_geopolitical_calendar()

    filters_row = st.columns((1, 2, 2, 1))
    with filters_row[1]:
        # Extract unique locations for the multiselect filter (assuming the 'Location' column exists)
        unique_locations = df['Location'].unique().tolist()
        # Use a multiselect widget for filtering by location
        selected_locations = st.multiselect('Filter by Location:', options=unique_locations,
                                            placeholder='All')
        if len(selected_locations) == 0:
            selected_locations = unique_locations

    with filters_row[2]:
        event_query = st.text_input('Search in Event:', '')

    filtered_df = df[df['Location'].isin(selected_locations)]
    if event_query:
        # If there's a query, further filter the DataFrame
        filtered_df = filtered_df[filtered_df['Event'].str.contains(event_query, case=False, na=False)]

    # Display the DataFrame as a table
    styler = filtered_df.style.hide()
    st.write(styler.to_html(escape=False), unsafe_allow_html=True)

if menu == "News":
    header = st.columns((3,1,3))
    header[1].write("### Port Pulse Updates")
    st.write("# ")
    df_news = extract_news()
    df_news = df_news.iloc[::-1].reset_index(drop=True)
    display_telegram_posts(df_news)
# -------------------------------------------------------------------------------------------------------
