import pandas as pd
import datetime

months_list = ['January', 'February', 'March', 'April', 'May', 'June',
               'July', 'August', 'September', 'October', 'November', 'December']


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


def filter_data(data: pd.DataFrame, location, depot):
    filtered_df = data.copy()
    if location:
        filtered_df = filtered_df[filtered_df["Location"].isin(location)]
    if depot:
        filtered_df = filtered_df[filtered_df["Depot"].isin(depot)]

    return filtered_df


def get_coi(filtered_df: pd.DataFrame,
            filtered_df_prev: pd.DataFrame):
    cost_of_inventory = filtered_df[filtered_df['Status'] != "SOLD"]['Value'].sum()
    previous_cost_of_inventory = filtered_df_prev[filtered_df_prev[
                                                      'Status'
                                                  ] != "SOLD"
                                                  ]['Value'].sum() if not filtered_df_prev.empty else 0
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
    gatein_aging = filtered_df['Inventory Aging'].mean()
    gatein_aging_prev = filtered_df_prev['Inventory Aging'].mean() if not filtered_df_prev.empty else 0
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


def news_card():
    return """
    <article class='news' style="background: "#b5e2fa";">
      <div class="content text">
        <small class="news--published">{published_at}</small>
        <h2>{title}</h2>
        <div class="body">
          <p>{description}</p>
        </div>
        <a aria-label="Read more" href="{url}">Read more<span aria-hidden="true" class="icon icon-arrow"></span></a>
      </div>
    </article>
    """
