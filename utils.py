import pandas as pd
import datetime
import plotly.graph_objects as go
import streamlit.components.v1 as components
import streamlit as st
import yfinance as yf

months_list = ['January', 'February', 'March', 'April', 'May', 'June',
               'July', 'August', 'September', 'October', 'November', 'December']



def load_data(conn, conn_2):
    data_sheet = conn.read(worksheet="Data_Sheet")
    data_sheet = preprocess_data(data_sheet[5:])

    weekly_data = conn.read(worksheet="Market pricing", header=2).dropna(how="all").fillna(0)

    location_data = conn.read(worksheet="Settings")
    location_data['Location Code'] = location_data['Location Code'].apply(
        lambda x: x[:-1] if x[-1].isdigit() else x
    )
    locations_map = location_data.set_index('Location Code')['Location'].to_dict()

    weekly_data["Location Name"] = weekly_data["Location"].map(locations_map)
    weekly_data = process_week_data(week_data=weekly_data)

    trading_pricing_data = conn_2.read(worksheet="Trading market price")
    trading_pricing_data['DATE'] = pd.to_datetime(trading_pricing_data['DATE'], errors='coerce')
    trading_pricing_data['Year'] = trading_pricing_data['DATE'].dt.year
    trading_pricing_data['Month'] = trading_pricing_data['DATE'].dt.month_name().str[:3]

    return data_sheet, weekly_data, trading_pricing_data


def process_week_data(week_data):
    cols = ["Size.1", "Location", "Condition", "Size", "Real Time", "On the way ",
            "Avg Market Price ", "AMMT Market Price ", "Location Name"]
    cols_map = {"Size.1": "Name", "Real Time": "Real Time", "On the way ": "On the way",
                "Avg Market Price ": "Avg Market Price", "AMMT Market Price ": "AMMT Market Price"}
    week_data = week_data[cols].rename(columns=cols_map)
    return week_data


def preprocess_data(data: pd.DataFrame):
    data.columns = data.columns.str.strip()
    data = format_datetime_column(data=data, columns=["Gate In", "Gate Out"])
    data = format_price_value(data=data, columns=["Value", "Sale Price", "Repair Cost",
                                                  "Storage Cost", "Purchase Cost"])
    data["Inventory Aging"] = data["Gate In"].apply(calculate_age_in_days)
    data["Dwell Time"] = (data["Gate Out"] - data["Gate In"]).dt.days
    data["Month"] = data["Gate In"].dt.month_name()
    data["Year"] = data["Gate In"].apply(extract_year)
    return data


def format_price_value(data: pd.DataFrame, columns: list):
    for i in columns:
        data[i] = pd.to_numeric(data[i].astype(str).str.replace('$', '').str.replace(',', ''), errors='coerce')
    return data


def format_datetime_column(data: pd.DataFrame, columns: list):
    for i in columns:
        data[i] = pd.to_datetime(data[i])
    return data


# Function to calculate the age in days
def calculate_age_in_days(gate_in_date):
    current_date = datetime.datetime.now()
    if pd.notna(gate_in_date):
        return (current_date - gate_in_date).days
    else:
        return 0


def format_kpi_value(kpi_value):
    if kpi_value >= 1e6:
        return f"${kpi_value / 1e6:.2f} M"
    elif kpi_value >= 1e3:
        return f"${kpi_value / 1e3:.2f} K"
    else:
        return f"${kpi_value:.2f}"


# Function to extract the year
def extract_year(date):
    if pd.notna(date):
        return date.year
    else:
        return 0


def get_filtered_data(df, location, depot, year):
    filtered_df_prev = df.copy()
    if location:
        df = df[df["Location"].isin(location)]
        filtered_df_prev = filtered_df_prev[filtered_df_prev["Location"].isin(location)]
    if depot:
        df = df[df["Depot"].isin(depot)]
        filtered_df_prev = filtered_df_prev[filtered_df_prev["Depot"].isin(depot)]

    filtered_df = df[df["Year"] == year]
    filtered_df_prev = filtered_df_prev[
        (filtered_df_prev["Gate In"] >= (pd.to_datetime(f"{year}-01-01") - pd.DateOffset(years=1))) &
        (filtered_df_prev["Gate In"] < pd.to_datetime(f"{year}-01-01"))
        ]
    return filtered_df, filtered_df_prev
















def pre_process_data(data: pd.DataFrame):
    data.columns = data.columns.str.strip()
    data = format_datetime_column(data=data, columns=["Gate In", "Gate Out"])
    data = format_price_value(data=data, columns=["Value", "Sale Price", "Repair Cost",
                                                  "Storage Cost", "Purchase Cost"])
    data["Inventory Aging"] = data["Gate In"].apply(calculate_age_in_days)
    data["Dwell Time"] = (data["Gate Out"] - data["Gate In"]).dt.days
    data["Month"] = data["Gate In"].dt.month_name()
    data["Year"] = data["Gate In"].apply(extract_year)
    return data





def filter_data(data: pd.DataFrame, location, depot):
    filtered_df = data.copy()
    if location:
        filtered_df = filtered_df[filtered_df["Location"].isin(location)]
    if depot:
        filtered_df = filtered_df[filtered_df["Depot"].isin(depot)]

    return filtered_df




def get_coi(filtered_df: pd.DataFrame,
            filtered_df_prev: pd.DataFrame):
    cost_of_inventory = filtered_df[filtered_df['Status'] != "SOLD"]['Purchase Cost'].sum()
    previous_cost_of_inventory = filtered_df_prev[filtered_df_prev[
                                                      'Status'
                                                  ] != "SOLD"
                                                  ]['Purchase Cost'].sum() if not filtered_df_prev.empty else 0
    percentage_change = ((cost_of_inventory - previous_cost_of_inventory) / previous_cost_of_inventory) \
                        * 100 if previous_cost_of_inventory != 0 else 0

    return cost_of_inventory, percentage_change


def get_inv_sold(filtered_df: pd.DataFrame,
                 filtered_df_prev: pd.DataFrame):
    inventory_sold = filtered_df[filtered_df['Status'] == "SOLD"]['Sale Price'].sum()
    previous_inventory_sold = filtered_df_prev[filtered_df_prev[
                                                   'Status'
                                               ] == "SOLD"
                                               ]['Sale Price'].sum() if not filtered_df_prev.empty else 0
    percentage_change = ((inventory_sold - previous_inventory_sold) / previous_inventory_sold) \
                        * 100 if previous_inventory_sold != 0 else 0

    return inventory_sold, percentage_change


def get_inv_under_repair(filtered_df: pd.DataFrame,
                         filtered_df_prev: pd.DataFrame):
    inv_under_repair = filtered_df['Repair Cost'].sum()
    inv_under_repair_prev = filtered_df_prev['Repair Cost'].sum() if not filtered_df_prev.empty else 0
    percentage_change = ((inv_under_repair - inv_under_repair_prev) / inv_under_repair_prev) \
                        * 100 if inv_under_repair_prev != 0 else 0

    return inv_under_repair, percentage_change


def get_inv_picked(filtered_df: pd.DataFrame,
                   filtered_df_prev: pd.DataFrame):
    inv_picked = len(filtered_df[filtered_df['Status'] == "PKUP"].index)
    inv_picked_prev = len(filtered_df_prev[
                              filtered_df_prev['Status'] == "PKUP"
                              ].index) if not filtered_df_prev.empty else 0
    percentage_change = ((inv_picked - inv_picked_prev) / inv_picked_prev) \
                        * 100 if inv_picked_prev != 0 else 0
    return inv_picked, percentage_change


def get_gatein_aging(filtered_df: pd.DataFrame,
                     filtered_df_prev: pd.DataFrame):
    gatein_aging = filtered_df['Aging'].mean()
    gatein_aging_prev = filtered_df_prev['Aging'].mean() if not filtered_df_prev.empty else 0
    percentage_change = ((gatein_aging - gatein_aging_prev) / gatein_aging_prev) \
                        * 100 if gatein_aging_prev != 0 else 0

    return gatein_aging, percentage_change


def get_dwell_time(filtered_df: pd.DataFrame,
                   filtered_df_prev: pd.DataFrame):
    dwell_time = filtered_df["Dwell Time"].mean()
    dwell_time_prev = filtered_df_prev["Dwell Time"].mean() if not filtered_df_prev.empty else 0
    percentage_change = ((dwell_time - dwell_time_prev) / dwell_time_prev) \
                        * 100 if dwell_time_prev != 0 else 0

    return dwell_time, percentage_change


def pre_process_trading_data(data):
    data['DATE'] = pd.to_datetime(data['DATE'], errors='coerce')
    data['MARKET_PRICE_USD'] = pd.to_numeric(data['MARKET_PRICE_USD'], errors='coerce')
    data['Month'] = data['DATE'].dt.month_name().str[:3]
    data['Year'] = data['DATE'].dt.year

    data['CONTAINER_CONDITION'] = data['CONTAINER_CONDITION'].apply(transform_container_condition_value)
    data['CONTAINER_TYPE'] = data['CONTAINER_TYPE'].apply(transform_container_condition_value)

    return data


# Function to transform each value
def transform_container_condition_value(value):
    if '_' in value:  # If underscore is present in the value
        words = value.split('_')
        # Capitalize each word and join them with a space
        return ' '.join(word.capitalize() for word in words)
    else:  # If the value is a single word
        return value.upper()  # Convert the value to uppercase


def display_telegram_posts(df):
    for index, row in df.iterrows():
        components.html(f"""
            <!DOCTYPE html>
            <html>
                <div>
                    <script async src="https://telegram.org/js/telegram-widget.js?22" data-telegram-post="{row['telegram_post_id']}" data-width="100%"></script>
                </div>
            </html>
            """,
                        height=row['div_height']
                        )


@st.cache_data
def get_commodities_data(ticker_name, commodities):
    # Initialize an empty list to store the data
    data_list = []

    # Fetch the data for each commodity
    for name, symbol in commodities.items():
        ticker = yf.Ticker(symbol)

        # Fetch data for the last two days to calculate daily changes
        hist_daily = ticker.history(period="5d")
        latest_close = None
        if len(hist_daily) >= 2:
            latest_close = hist_daily['Close'].iloc[-1]
            previous_close = hist_daily['Close'].iloc[-2]
            daily_point_change = latest_close - previous_close
            daily_percent_change = round((daily_point_change / previous_close) * 100, 2)
        else:
            daily_point_change = daily_percent_change = None

        # Fetch historical data for the trend
        hist_trend = ticker.history(period="1mo")
        trend_data = hist_trend['Close'].tolist()

        data_list.append([
            name, latest_close, daily_point_change, daily_percent_change, trend_data
        ])

    # DataFrame from the collected data
    df = pd.DataFrame(data_list, columns=[
        f"{ticker_name}", "Price", "Daily Change", "%age Diff", "Trend"
    ])
    df = df.dropna()

    df["%age Diff"] = df["%age Diff"].apply(lambda x: str(round(x, 3))+"%")

    return df


def commodities_table(df):
    def color_cells(val):
        color = '#81b29a' if val[0] != '-' else '#f07167'
        return f'background-color: {color}'

    df["bgColor"] = df["DaysRemainingCode"].map({
        "Red": "#e76f51",
        "Yellow": "#e9c46a",
        "Green": "#52b788"
    })

    styler = df.style.applymap(color_cells, subset=["%age Diff"])
    fig = go.Figure(
        data=[go.Table(
        columnwidth=[2, 2, 2, 2, 5],
        header=dict(
            values=list(df.columns),
            font=dict(size=14, color='white', family='ubuntu'),
            fill_color='#264653',
            align=['center'],
            height=80
        ),
        cells=dict(
            values=[df[K].tolist() for K in df.columns],
            font=dict(size=12, color="black", family='ubuntu'),
            fill_color=['#f5ebe0', '#f5ebe0', '#f5ebe0', '#f5ebe0',
                        df["DaysRemainingColor"].values, '#f5ebe0'],
            align=['center'],
            height=80
        ))]
    )
    fig.update_layout(margin=dict(l=0, r=10, b=10, t=30), height=500)
    return fig



# @st.cache_data
# def get_commodities_data(ticker_name, commodities):
#     # Initialize an empty list to store the data
#     data_list = []
#
#     # Fetch the data for each commodity
#     for name, symbol in commodities.items():
#         ticker = yf.Ticker(symbol)
#
#         # Fetch data for the last two days to calculate daily changes
#         hist_daily = ticker.history(period="2d")
#         latest_close = None
#         if len(hist_daily) >= 2:
#             latest_close = hist_daily['Close'].iloc[-1]
#             previous_close = hist_daily['Close'].iloc[-2]
#             daily_point_change = latest_close - previous_close
#             daily_percent_change = round((daily_point_change / previous_close) * 100, 2)
#         else:
#             daily_point_change = daily_percent_change = None
#
#         # Fetch data for the last two weeks and resample to weekly frequency to calculate weekly changes
#         hist_weekly = ticker.history(period="1mo")
#         hist_weekly.index = pd.to_datetime(hist_weekly.index)
#         hist_weekly = hist_weekly['Close'].resample('W-FRI').last().dropna()
#         if len(hist_weekly) >= 2:
#             last_week_close = hist_weekly.iloc[-1]
#             prev_week_close = hist_weekly.iloc[-2]
#             weekly_change = round(((last_week_close - prev_week_close) / prev_week_close) * 100, 2)
#         else:
#             weekly_change = None
#
#         # Fetch data for the last two months and resample to monthly frequency to calculate monthly changes
#         hist_monthly = ticker.history(period="1y")
#         hist_monthly.index = pd.to_datetime(hist_monthly.index)
#         hist_monthly = hist_monthly['Close'].resample('M').last().dropna()
#         if len(hist_monthly) >= 2:
#             last_month_close = hist_monthly.iloc[-1]
#             prev_month_close = hist_monthly.iloc[-2]
#             monthly_change = round(((last_month_close - prev_month_close) / prev_month_close) * 100, 2)
#         else:
#             monthly_change = None
#
#         # Fetch data for the last two years and resample to yearly frequency to calculate yearly changes
#         hist_yearly = ticker.history(period="2y")
#         hist_yearly.index = pd.to_datetime(hist_yearly.index)
#         hist_yearly = hist_yearly['Close'].resample('A').last().dropna()
#         if len(hist_yearly) >= 2:
#             last_year_close = hist_yearly.iloc[-1]
#             prev_year_close = hist_yearly.iloc[-2]
#             yearly_change = round(((last_year_close - prev_year_close) / prev_year_close) * 100, 2)
#         else:
#             yearly_change = None
#
#         # Fetch historical data for the trend
#         hist_trend = ticker.history(period="1mo")
#         trend_data = hist_trend['Close'].tolist()
#
#         data_list.append([
#             name, latest_close, daily_point_change, daily_percent_change,
#             weekly_change, monthly_change, yearly_change, trend_data
#         ])
#
#     # DataFrame from the collected data
#     df = pd.DataFrame(data_list, columns=[
#         f"{ticker_name}", "Price", "Daily Change", "%age Diff",
#         "Weekly Change", "Monthly Change", "Yearly Change", "Trend"
#     ])
#     df = df.dropna()
#
#     df["%age Diff"] = df["%age Diff"].apply(lambda x: str(round(x, 3))+"%")
#     df["Weekly Change"] = df["Weekly Change"].apply(lambda x: str(round(x, 3))+"%")
#     df["Monthly Change"] = df["Monthly Change"].apply(lambda x: str(round(x, 3))+"%")
#     df["Yearly Change"] = df["Yearly Change"].apply(lambda x: str(round(x, 3))+"%")
#
#     return df
