import pandas as pd
import streamlit as st
from plotly.subplots import make_subplots

from css.st_ui import plotly_svg_css_2, plotly_svg_css_1
from plots import format_hover_layout, get_weekly_data_table, \
    container_prices_wrt_location, container_count_plot, container_prices_plot, get_market_price_map, \
    biggest_growth_and_drop_in_prices, sales_overtime, sold_inv_dist, gate_in_out_distribution, top_customers, \
    commodities_info, container_prices_and_count, get_wci_chart
from scraper.calendar_scraper import get_geopolitical_calendar
from scraper.news_scraper import extract_news
from scraper.wci_scraper import get_wci_data
from utils import get_filtered_data, get_coi, get_inv_sold, get_inv_under_repair, get_inv_picked, get_gatein_aging, \
    get_dwell_time, format_kpi_value, display_telegram_posts

from const import Commodities

import plotly.graph_objects as go


colors = ["#264653", "#2a9d8f", "#e9c46a", "#f4a261", "#e76f51", "#84a59d", "#006d77",
          "#f6bd60", "#90be6d", "#577590", "#e07a5f", "#81b29a", "#f2cc8f", "#0081a7"]


def overview_page(week_data):
    st.markdown(plotly_svg_css_1, unsafe_allow_html=True)
    with st.sidebar:
        loc = st.multiselect(label="Location", options=set(week_data["Location Name"].dropna().values), placeholder="All")
        if not loc:
            loc = set(week_data["Location Name"].dropna().values)

        size = st.multiselect(label="Size", options=set(week_data["Size"].dropna().values), placeholder="All")
        if not size:
            size = set(week_data["Size"].dropna().values)

        condition = st.multiselect(label="Condition", options=set(week_data["Condition"].dropna().values), placeholder="All")
        if not condition:
            condition = set(week_data["Condition"].dropna().values)

    filtered_week_df = week_data[(week_data["Location Name"].isin(loc)) &
                                 (week_data["Size"].isin(size)) &
                                 (week_data["Condition"].isin(condition))]

    cols_of_interest = ["Real Time", "On the way", "Avg Market Price", "AMMT Market Price"]
    filtered_week_df = filtered_week_df[~((filtered_week_df[cols_of_interest] == 0) |
                                          (filtered_week_df[cols_of_interest].isna())).all(axis=1)].drop(columns=["Location Name"], axis=1)


    kpis_row = st.columns(5)

    kpis_row[0].metric(label="Total Containers", value=int(filtered_week_df["Real Time"].sum()))
    kpis_row[1].metric(label="Containers On the Way", value=int(filtered_week_df["On the way"].sum()))
    kpis_row[2].metric(label="Avg Market Price", value=format_kpi_value(filtered_week_df[filtered_week_df["Avg Market Price"]>0]["Avg Market Price"].mean()))
    kpis_row[3].metric(label="AMMT Market Price", value=format_kpi_value(filtered_week_df[filtered_week_df["AMMT Market Price"]>0]["AMMT Market Price"].mean()))
    kpis_row[4].metric(label="Total Market Price", value=format_kpi_value(filtered_week_df[filtered_week_df["AMMT Market Price"]>0]["AMMT Market Price"].sum()))


    st.plotly_chart(get_weekly_data_table(df=filtered_week_df), use_container_width=True)


def sales_analytics_page(data):
    st.markdown(plotly_svg_css_2, unsafe_allow_html=True)
    # ------------------------ Filters ------------------------------------------------
    location = st.sidebar.multiselect(label="Location", options=set(data["Location"].dropna().values), placeholder="All")
    depot = st.sidebar.multiselect(label="Depot", options=set(data["Depot"].dropna().values), placeholder="All")
    year = st.sidebar.selectbox(label="Year", options=sorted(list(data["Year"].unique())), index=2)

    # Filtered Data
    filtered_df, filtered_df_prev = get_filtered_data(data, location, depot, year)

    # ------------------------- Main Display ---------------------------------------
    if len(filtered_df) == 0:
        st.warning("No Data Record found.")
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

    kpi_row[4].metric(label="Inv Aging",  # Aging of Inventory (Gate In to Today)
                      value=f"{gatein_aging:.1f} days",
                      delta=f"{percentage_change_gia:.1f}%")
    try:
        kpi_row[5].metric(label="Dwell Time",  # Dwell Time (Gate In to Sell Date)
                          value=f"{int(dwell_time)} days",
                          delta=f"{percentage_change_dt:.1f}%")
    except ValueError:
        kpi_row[5].metric(label="Dwell Time",  # Dwell Time (Gate In to Sell Date)
                          value=f"{0} days",
                          delta=f"{percentage_change_dt:.1f}%")

    charts_row = st.columns((2,1))
    charts_row[0].plotly_chart(sales_overtime(data, location, depot), use_container_width=True)
    charts_row[1].plotly_chart(sold_inv_dist(data, location, depot), use_container_width=True)

    charts_row[0].plotly_chart(gate_in_out_distribution(data, location, depot), use_container_width=True)
    charts_row[1].plotly_chart(top_customers(data, location, depot), use_container_width=True)

def trading_prices_page(df_trading):
    st.markdown(plotly_svg_css_2, unsafe_allow_html=True)
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


def calendar_page():
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


def commodities_page(df_trading):
    st.markdown(plotly_svg_css_1, unsafe_allow_html=True)

    row_1 = st.columns((5,3))
    with row_1[0]:
        inner_cols = st.columns(3)
        selected_city = inner_cols[0].selectbox(label="Location", options=df_trading['CITY'].unique())
        data = df_trading[df_trading['CITY'] == selected_city]

        time_period = inner_cols[1].selectbox(label="Range", options=['All', 'YTD', '6m', '1y', '2y'], index=0)
        today = pd.to_datetime("today")
        if time_period == 'YTD':
            start_date = pd.to_datetime(f"{today.year}-01-01")
        elif time_period == '6m':
            start_date = today - pd.DateOffset(months=6)
        elif time_period == '1y':
            start_date = today - pd.DateOffset(years=1)
        elif time_period == '2y':
            start_date = today - pd.DateOffset(years=2)
        else:
            start_date = None
        if start_date:
            data = data[data['DATE'] >= start_date]

    row_1[0].plotly_chart(container_prices_and_count(data), use_container_width=True)

    wci_data = get_wci_data()
    # row_1[1].dataframe(wci_data)
    row_1[1].plotly_chart(get_wci_chart(wci_data), use_container_width=True)

    commodities_info(Commodities)


def news_page():
    header = st.columns((3,1,3))
    header[1].write("### Port Pulse Updates")
    st.write("# ")
    df_news = extract_news()
    df_news = df_news.iloc[::-1].reset_index(drop=True)
    display_telegram_posts(df_news)
