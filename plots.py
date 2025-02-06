import pandas as pd
import streamlit as st
import datetime
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from utils import get_commodities_data

colors = ["#264653", "#2a9d8f", "#e9c46a", "#f4a261", "#e76f51", "#84a59d", "#006d77",
          "#f6bd60", "#90be6d", "#577590", "#e07a5f", "#81b29a", "#f2cc8f", "#0081a7"]

months_list = ['January', 'February', 'March', 'April', 'May', 'June',
               'July', 'August', 'September', 'October', 'November', 'December']


def get_weekly_data_table(df):
    for col in df.columns:
        if "Price" in col:
            df[col] = df[col].apply(lambda x: f"${x:.2f}")
    fill_colors =  ["#778da9", "#415a77"] * len(df)
    fill_colors = ["#2f3e46", "#354f52", "#52796f"] * len(df)
    fill_colors = fill_colors[:len(df)]

    # Function to determine font color based on value
    def get_font_color(column_values):
        return ["#e63946" if val == 0 else "#52b788" for val in column_values]

    ammt_market_price_values = df["AMMT Market Price"].tolist()
    avg_market_price_values = df["Avg Market Price"].tolist()
    ammt_market_price_display = [
        f"🔺 {value}" if value > avg_market_price_values[i] else str(value)
        for i, value in enumerate(ammt_market_price_values)
    ]

    # Get font colors for "Real Time" and "On the way" columns
    real_time_font_color = get_font_color(df["Real Time"])
    on_the_way_font_color = get_font_color(df["On the way"])
    fig = go.Figure(data=[go.Table(
        columnwidth=[2, 2, 2, 2, 2, 2, 2, 2],
        header=dict(
            values=["🏷️ Name", "📍 Location", "🔍 Condition", "📏 Size" , "⏳ Real Time", "🚛 On the way", "💰 Avg Market Price", "📈 AMMT Market Price"],
            fill_color="#1b263b",
            font=dict(family="ubuntu", color="#adb5bd", size=18, weight="bold"),
            align="center",
            line_color="black",
            height=50,
            line_width=0,
        ),
        cells=dict(
            values=[
                df["Name"].tolist(),
                df["Location"].tolist(),
                df["Condition"].tolist(),
                df["Size"].tolist(),
                df["Real Time"].tolist(),
                df["On the way"].tolist(),
                df["Avg Market Price"].tolist(),
                ammt_market_price_display  # Use the modified "AMMT Market Price" values
            ],
            fill_color=[fill_colors * len(df.columns)],
            font=dict(family="ubuntu", color="#ced4da", size=14, weight="bold"),
            align="center",
            height=45,
            line_width=0,
            line_color="black"
        )
    )])

    fig.update_traces(
        cells=dict(
            font=dict(
                color=[["white"] * len(df)] * (df.columns.get_loc("Real Time")) +  # Default white for columns before "Real Time"
                      [real_time_font_color] +  # Font color for "Real Time"
                      [["white"] * len(df)] * (df.columns.get_loc("On the way") - df.columns.get_loc("Real Time") - 1) +  # Default white for columns between "Real Time" and "On the way"
                      [on_the_way_font_color] +  # Font color for "On the way"
                      [["white"] * len(df)] * (len(df.columns) - df.columns.get_loc("On the way") - 1)  # Default white for columns after "On the way"
            )
        )
    )

    fig.update_layout(margin=dict(l=10, r=0, t=20, b=20), height=60*(len(df)+2))

    return fig


def sales_overtime(data, location, depot):
    if not location:
        location = set(data['Location'])
    if not depot:
        depot = set(data['Depot'])
    data = data[(data['Location'].isin(location)) & (data['Depot'].isin(depot))]
    data['Gate Out'] = pd.to_datetime(data['Gate Out'], errors='coerce')
    data['Month-Year'] = data['Gate Out'].dt.strftime('%b %y')

    sold_data = data[data['Status'] == 'SOLD']
    sold_over_time = sold_data.groupby('Month-Year')['Sale Price'].sum().reset_index()
    sold_over_time['Month-Year'] = pd.to_datetime(sold_over_time['Month-Year'], format='%b %y')
    sold_over_time = sold_over_time[sold_over_time['Month-Year'] <= datetime.datetime.today()]
    sold_over_time = sold_over_time.sort_values(by='Month-Year')

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=sold_over_time['Month-Year'],
        y=sold_over_time['Sale Price'],
        mode='lines',
        fill='tozeroy',
        fillcolor='rgba(0,100,80,0.2)',
        name='Total Sale Price',
        line=dict(color='#2a9d8f'),
        hovertemplate='Total Sales = $%{y:.2f}'
    ))

    fig.update_layout(
        title='Sales Over Time',
        # xaxis_title='Time',
        yaxis_title='Sale Price',
    )
    fig = format_hover_layout(fig)

    return fig


def sold_inv_dist(data, location, depot):
    if not location:
        location = set(data['Location'])
    if not depot:
        depot = set(data['Depot'])
    data = data[(data['Location'].isin(location)) & (data['Depot'].isin(depot))]

    sold_data = data[data['Status'] == 'SOLD']

    sales_dist = sold_data.groupby('Size')['Unit #'].count().reset_index()
    sales_dist = sales_dist.sort_values(by='Unit #', ascending=False)

    top_5 = sales_dist.head(5)
    other = sales_dist.tail(len(sales_dist) - 5).sum()
    other['Size'] = 'Other'  # Assign 'Other' to the aggregated row

    sales_dist = pd.concat([top_5, other.to_frame().T], ignore_index=True)

    fig = go.Figure()
    fig.add_trace(go.Pie(
        labels=sales_dist['Size'],
        values=sales_dist['Unit #'],
        hole=0.4,
        textinfo='percent+label',
        hoverinfo='label+value+percent',
        hovertemplate='Size: %{label}<br>Total Units: %{value} (%{percent})'
    ))
    fig.update_traces(marker=dict(colors=['#006d77', '#83c5be', '#ffddd2', '#e29578', '#fed9b7', '#caf0f8']))
    fig.update_layout(
        title='Sales Distribution by Size',
        showlegend=True
    )

    fig = format_hover_layout(fig)

    return fig


def gate_in_out_distribution(data, location, depot):
    if not location:
        location = set(data['Location'])
    if not depot:
        depot = set(data['Depot'])

    data = data[(data['Location'].isin(location)) & (data['Depot'].isin(depot))]

    data['Gate In'] = pd.to_datetime(data['Gate In'], errors='coerce')
    data['Gate Out'] = pd.to_datetime(data['Gate Out'], errors='coerce')

    data['Month-Year In'] = data['Gate In'].dt.strftime('%b %y')
    data['Month-Year Out'] = data['Gate Out'].dt.strftime('%b %y')

    gate_in_count = data.groupby('Month-Year In').size().reset_index(name='Gate In Count')
    gate_out_count = data.groupby('Month-Year Out').size().reset_index(name='Gate Out Count')

    merged_counts = pd.merge(gate_in_count, gate_out_count, left_on='Month-Year In', right_on='Month-Year Out', how='outer')
    merged_counts['Month-Year'] = merged_counts['Month-Year In'].fillna(merged_counts['Month-Year Out'])
    merged_counts['Month-Year'] = pd.to_datetime(merged_counts['Month-Year'], format='%b %y')
    merged_counts = merged_counts[merged_counts['Month-Year'] <= datetime.datetime.today()]
    merged_counts = merged_counts.sort_values(by='Month-Year')
    # merged_counts = merged_counts.sort_values('Month-Year')

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=merged_counts['Month-Year'],
        y=merged_counts['Gate In Count'],
        name='Gate In Count',
        marker=dict(color='#2a9d8f'),
    ))

    fig.add_trace(go.Bar(
        x=merged_counts['Month-Year'],
        y=merged_counts['Gate Out Count'],
        name='Gate Out Count',
        marker=dict(color='#264653')
    ))

    fig.update_layout(
        title='Gate In and Gate Out Distribution Over Time',
        # xaxis_title='Month-Year',
        yaxis_title='Count',
        barmode='group'
    )
    fig = format_hover_layout(fig)

    return fig



def top_customers(data, location, depot):
    if not location:
        location = set(data['Location'])
    if not depot:
        depot = set(data['Depot'])

    data = data[(data['Location'].isin(location)) & (data['Depot'].isin(depot))]
    customer_counts = data.groupby('Customer').size().reset_index(name='Item Count')
    top_8_customers = customer_counts.sort_values(by='Item Count', ascending=False).head(8)
    top_8_customers = top_8_customers.sort_values(by='Item Count', ascending=True)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=top_8_customers['Customer'],
        x=top_8_customers['Item Count'],
        orientation='h',
        name = 'Customer',
        hovertemplate='%{y}<br><b>Purchase Freq: %{x}<b>',
        marker=dict(color='#264653')
    ))

    fig.update_layout(
        title='Top Customers',
        xaxis_title='Customer',
        yaxis_title='Sales Count',
    )
    fig = format_hover_layout(fig)

    return fig



# ------------------------- Macro ------------------------------------------------------------

def container_prices_and_count(data):
    data['MONTH_YEAR'] = data['DATE'].dt.to_period('M')
    data = data.groupby(['MONTH_YEAR', 'CITY']).agg({'MARKET_PRICE_USD': "sum",
                                                     "CONTAINER_COUNT": "sum"}).reset_index()
    data = data.sort_values(by='MONTH_YEAR')
    data['MONTH_YEAR'] = data['MONTH_YEAR'].dt.strftime('%b %Y')

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Bar(
            x=data["MONTH_YEAR"], y=data["MARKET_PRICE_USD"],
            name='Price',
            marker=dict(color=colors[0]),
            hovertemplate='$%{y}'
        ),
        secondary_y=False
    )

    fig.add_trace(
        go.Scatter(
            x=data['MONTH_YEAR'],
            y=data['CONTAINER_COUNT'],
            name='Listed Containers #',
            mode="markers+lines",
            marker=dict(color='#e9c46a'),
            hovertemplate='Num of Containers: %{y:.2f}<extra></extra>'
        ),
        secondary_y=True
    )
    fig.update_layout(
        title='Container Prices & Count overtime',
        xaxis_title='Date',
        yaxis_title="Container Prices",
        legend_title="Sales Location",
        legend=dict(orientation="h", xanchor='center', x=0.5, y=-0.25))
    fig = format_hover_layout(fig)
    fig.update_layout(
        height=440
    )
    return fig


def commodities_info(commodities):
    for i in commodities:
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
        st.data_editor(
            df,
            column_config=col_config,
            hide_index=True,
            use_container_width=True
        )


def get_wci_chart(df):
    fill_colors =  ["#eff6e0", "#aec3b0"] * len(df)
    # fill_colors = ["#2f3e46", "#354f52", "#52796f"] * len(df)
    fill_colors = fill_colors[:len(df)]
    df['Annual change (%)'] = df['Annual change (%)'].apply(lambda x: f"🔻{x}" if x.split()[0] == "Down" else f"📈{x}")

    fig = go.Figure(data=[go.Table(
        columnwidth=[2, 2, 2, 2, 2, 2, 2, 2],
        header=dict(
            values=df.columns,
            fill_color="#124559",
            font=dict(family="ubuntu", color="white", size=18, weight="bold"),
            align="center",
            line_color="black",
            height=50,
            line_width=0,
        ),
        cells=dict(
            values=[df[col] for col in df.columns],
            fill_color=[fill_colors * len(df.columns)],
            font=dict(family="ubuntu", color="black", size=14, weight="bold"),
            align="center",
            height=45,
            line_width=0,
            line_color="black"
        )
    )])

    fig.update_layout(margin=dict(l=0, r=0, t=10, b=5), height=60*(len(df)))

    return fig


# ------------------------- Prev ---------------------------------------------------------------

def available_for_sale_plot(data):
    fig = go.Figure()
    i = 0
    for size in data.columns:
        fig.add_trace(
            go.Bar(x=data.index, y=data[size], name=size, marker=dict(color=colors[i])))
        i += 1

    fig.update_layout(barmode='group', xaxis_title='Depot', yaxis_title='Units Available for Sale',
                      title='DIST. OF INVENTORY AVAILABLE FOR SALE',
                      xaxis={'categoryorder': 'total ascending'},
                      legend_title="Size")
    fig = format_hover_layout(fig)

    return fig


def sold_inventory_plot(data):
    fig = go.Figure()
    i = 0
    for size in data.columns:
        non_zero_data = data[data[size] > 0]
        if not non_zero_data.empty:
            fig.add_trace(
                go.Bar(x=data.index, y=data[size], name=size, marker=dict(color=colors[i])))
            i += 1

    fig.update_layout(barmode='stack', xaxis_title='Depot', yaxis_title='# Units Sold',
                      title='SOLD INVENTORY DISTRIBUTION',
                      xaxis={'categoryorder': 'total ascending'},
                      legend_title="Size")
    fig = format_hover_layout(fig)

    return fig


def inventory_avb_breakdown_plot(avb_inventory):
    # Group the data by 'Size' and 'Condition Status'
    inventory_grouped = avb_inventory.groupby(['Size', 'Condition']).size().reset_index(name='Count')

    # Get the list of all unique sizes and conditions for the plot
    sizes = inventory_grouped['Size'].unique()
    conditions = inventory_grouped['Condition'].unique()

    # Create the figure
    fig = go.Figure()

    ind = 0
    # Add a bar trace for each condition
    for condition in conditions:
        filtered_data = inventory_grouped[inventory_grouped['Condition'] == condition]
        fig.add_trace(go.Bar(
            x=filtered_data['Size'],
            y=filtered_data['Count'],
            name=condition,
            text=filtered_data['Count'],
            marker=dict(color=colors[ind]),
        ))
        ind += 1

    # Update the layout
    fig.update_layout(
        barmode='group',
        title='BREAKDOWN OF INVENTORY AVAILABLE FOR SALE',
        xaxis_title='Size',
        yaxis_title='Items Count',
        hovermode="x unified",
        legend_title_text='Condition',
        legend=dict(orientation="h", xanchor='center', x=0.5, y=-0.25)
    )

    fig = format_hover_layout(fig)

    return fig


def monthly_sales_plot(data):
    fig = go.Figure()
    # Iterate over unique 'Size' values
    i = 0
    for size in data['Size'].unique():
        df_size = data[data['Size'] == size]
        df_size = pd.DataFrame(df_size.groupby("Month")["Sale Price"].sum())
        df_size = df_size.reindex(months_list, axis=0)
        df_size.reset_index(inplace=True)
        fig.add_trace(go.Scatter(
            x=df_size['Month'],
            y=df_size['Sale Price'],
            text=df_size['Sale Price'],
            mode='lines+markers+text',
            textposition='top center',
            name=size,
            marker=dict(color=colors[i]),
            line=dict(color=colors[i])
        ))
        i += 1
    fig.update_layout(title="Sales by Month", xaxis_title="Months", yaxis_title="Sales",
                      legend_title="Size")
    fig = format_hover_layout(fig)

    return fig


def sales_cost_breakdown_plot(data):
    fig = go.Figure()
    i = 0
    for cost in data.columns:
        fig.add_trace(go.Bar(x=data.index, y=data[cost], name=cost, marker=dict(color=colors[i])))
        i += 1
    fig.update_layout(
        title="AVG. YEARLY SALES VS. COST BREAKDOWN",
        xaxis_title="Months", yaxis_title="Cost", barmode='stack',
        legend_title="Cost"
    )
    fig = format_hover_layout(fig)

    return fig


def inventory_plot(data):
    fig = go.Figure()
    fig.add_trace(
        go.Bar(x=data["Month"], y=data["Gate In"], name="Gate In Items",
               marker=dict(color="#2a9d8f"))
    )
    fig.add_trace(
        go.Bar(x=data["Month"], y=data["Gate Out"], name="Gate Out Items",
               marker=dict(color="#e63946"))
    )
    fig.update_layout(
        barmode='group',  # This combines positive and negative bars for each month
        title='Gate In vs. Gate Out over-time',
        xaxis_title='Month',
        yaxis_title='Items Count',
        showlegend=False)
    fig = format_hover_layout(fig)

    return fig


def inventory_per_depot(data):
    fig = go.Figure()
    fig.add_trace(
        go.Bar(x=data["Depot"], y=data["Gate In"], name="Gate In Items",
               marker=dict(color="#2a9d8f"))
    )
    fig.add_trace(
        go.Bar(x=data["Depot"], y=data["Gate Out"], name="Gate Out Items",
               marker=dict(color="#e63946"))
    )
    fig.update_layout(
        barmode='group',  # This combines positive and negative bars for each month
        title='Gate In vs. Gate Out w.r.t Depot',
        xaxis_title='Depot',
        yaxis_title='Items Count',
        hovermode="x unified",
        showlegend=False)
    fig = format_hover_layout(fig)

    return fig


def shipping_costs_plot(data, size):
    fig = go.Figure()
    fig.add_trace(
        go.Bar(x=data["Port"], y=data[size],
               marker=dict(color="#264653"),
               hovertemplate='$%{y}',
               name='Shipping Cost'
               )
    )
    fig.update_layout(
        title='Shipping Container Costs From Western US',
        xaxis_title='Port',
        yaxis_title=f"Amount($)",
        hovermode="x unified",
        showlegend=False,
        height=400)
    fig = format_hover_layout(fig)
    return fig


def container_prices_plot(data):
    # Group by month and year, and sum the container counts
    data['MONTH_YEAR'] = data['DATE'].dt.to_period('M')
    data = data.groupby(['MONTH_YEAR', 'CITY']).agg({'MARKET_PRICE_USD': "sum",
                                                     "CONTAINER_COUNT": "sum"}).reset_index()

    # Sort the data by 'MONTH_YEAR'
    data = data.sort_values(by='MONTH_YEAR')

    # Convert 'MONTH_YEAR' to the desired string format for plotting
    data['MONTH_YEAR'] = data['MONTH_YEAR'].dt.strftime('%b %Y')

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    ind = 0
    for loc in data["CITY"].unique():
        filtered_df1 = data[data["CITY"] == loc]
        fig.add_trace(
            go.Bar(
                x=filtered_df1["MONTH_YEAR"], y=filtered_df1["MARKET_PRICE_USD"],
                name=loc,
                marker=dict(color=colors[ind]),
                hovertemplate='$%{y}'
            ),
            secondary_y=False
        )
        ind += 1

    fig.add_trace(
        go.Scatter(
            x=data['MONTH_YEAR'],
            y=data['CONTAINER_COUNT'],
            name='Listed Containers #',
            mode="markers+lines",
            marker=dict(color='#e9c46a'),
            hovertemplate='Num of Containers: %{y:.2f}<extra></extra>'
        ),
        secondary_y=True
    )
    fig.update_layout(
        title='Container Prices & Count overtime',
        xaxis_title='Date',
        yaxis_title="Container Prices",
        legend_title="Sales Location",
        legend=dict(orientation="h", xanchor='center', x=0.5, y=-0.25))
    fig = format_hover_layout(fig)
    fig.update_layout(
        height=440
    )
    return fig


def container_count_plot(data):
    # Group by month and year, and sum the container counts
    data['MONTH_YEAR'] = data['DATE'].dt.to_period('M')
    data = data.groupby('MONTH_YEAR')['CONTAINER_COUNT'].sum().reset_index()

    # Sort the data by 'MONTH_YEAR'
    data = data.sort_values(by='MONTH_YEAR')

    data['Month-to-Month Change'] = data['CONTAINER_COUNT'].pct_change() * 100
    data['Month-to-Month Change'] = data['Month-to-Month Change'].fillna(0)
    # Convert 'MONTH_YEAR' to the desired string format for plotting
    data['MONTH_YEAR'] = data['MONTH_YEAR'].dt.strftime('%b %Y')

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Bar(
            x=data['MONTH_YEAR'],
            y=data['CONTAINER_COUNT'],
            name='Listed Count',
            marker=dict(color='#287271'),
            hovertemplate='%{y:.0f}'
        ),
        secondary_y=False
    )

    fig.add_trace(
        go.Scatter(
            x=data['MONTH_YEAR'],
            y=data['Month-to-Month Change'],
            name='Month-to-Month Change',
            mode="markers+lines",
            marker=dict(color='#e9c46a'),
            hovertemplate='Percentage Change: %{y:.2f}%<extra></extra>'
        ),
        secondary_y=True
    )
    fig.update_layout(title='Listed Container Count',
                      xaxis_title='Time', yaxis_title='Container Count',
                      legend=dict(orientation="h", xanchor='center', x=0.5, y=-0.25))
    fig = format_hover_layout(fig)

    return fig


def get_market_price_map(data):
    month_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    # Ensure months are in chronological order
    month_to_number = {
        'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
        'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
    }
    df_agg = data.groupby(['Year', 'Month']).agg({'MARKET_PRICE_USD': 'sum'}).reset_index()
    df_agg['MonthNumber'] = df_agg['Month'].map(month_to_number)
    df_agg_sorted = df_agg.sort_values(by=['MonthNumber'])

    heatmap_data = df_agg_sorted.pivot(index="Month", columns="Year", values="MARKET_PRICE_USD")
    unique_months = heatmap_data.index.tolist()
    new_index = [month for month in month_order if month in unique_months]
    heatmap_data = heatmap_data.reindex(new_index)
    # heatmap_data = heatmap_data.fillna(0)
    fig = px.imshow(
        heatmap_data,
        labels=dict(x="Year", y="Month", color="Market Price (USD)"),
        x=heatmap_data.columns,  # Year
        y=heatmap_data.index,  # Month
        aspect="auto",
        title="Market Price Map",
        color_continuous_scale='Emrld',
    )

    # Display the price value inside each box
    fig.update_traces(text=heatmap_data.values, texttemplate="%{text:.0f}")

    # Update the layout
    fig.update_layout(
        xaxis_title='Year',
        yaxis_title='Month',
        xaxis=dict(tickmode='array', tickvals=heatmap_data.columns, ticktext=[int(x) for x in heatmap_data.columns]),
        yaxis=dict(tickmode='array', tickvals=heatmap_data.index),
        coloraxis_showscale=False
    )

    # Update xaxis type to be 'category' to avoid non-integer values on axis
    fig.update_xaxes(type='category')

    # Remove grid lines
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=False)

    return fig


def container_prices_wrt_location(data):
    # Group by city, and sum the container prices
    data = data.groupby('CITY')['MARKET_PRICE_USD'].sum().reset_index()

    # Sort the data by 'MARKET_PRICE_USD'
    data = data.sort_values(by='MARKET_PRICE_USD')

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=data['MARKET_PRICE_USD'],
            y=data['CITY'],
            name='Net Container Price',
            marker=dict(color='#287271'),
            hovertemplate='$%{x:.0f}',
            orientation='h'
        )
    )

    fig.update_layout(title='Container Prices w.r.t Location',
                      xaxis_title='Container Price, $', yaxis_title='City')
    fig = format_hover_layout(fig)

    return fig


def biggest_growth_and_drop_in_prices(data):
    # Group by CITY and DATE, and sum the market prices
    grouped_data = data.groupby(['CITY', pd.Grouper(key='DATE', freq='W-Mon')])[
        'MARKET_PRICE_USD'].sum().reset_index()

    # Calculate the week-on-week change
    grouped_data['Week-on-Week Change'] = grouped_data.groupby('CITY')['MARKET_PRICE_USD'].pct_change()

    # Filter out the first week for each city
    grouped_data = grouped_data.dropna()

    grouped_data = grouped_data[['CITY', 'MARKET_PRICE_USD', 'Week-on-Week Change']].rename(
        columns={'CITY': 'City Area', 'MARKET_PRICE_USD': 'Market Price'}
    )
    grouped_data['Market Price'] = grouped_data['Market Price'].astype(int)

    # Identify locations with the biggest week-on-week growth and drop
    biggest_growth = grouped_data.sort_values(by='Week-on-Week Change', ascending=False).drop_duplicates(
        subset='City Area')
    biggest_drop = grouped_data.sort_values(by='Week-on-Week Change', ascending=True).drop_duplicates(
        subset='City Area')

    biggest_growth['Week-on-Week Change'] = biggest_growth['Week-on-Week Change'].apply(
        lambda x: str(round(x, 2)) + "%")
    biggest_growth['Market Price'] = biggest_growth['Market Price'].apply(lambda x: '$'+str(x))
    biggest_drop['Week-on-Week Change'] = biggest_drop['Week-on-Week Change'].apply(lambda x: str(round(x, 2)) + "%")
    biggest_drop['Market Price'] = biggest_drop['Market Price'].apply(lambda x: '$'+str(x))

    return biggest_growth, biggest_drop


def prices_variation_chart(data, indicator, table_title):
    fig = go.Figure(data=[go.Table(
        columnwidth=[1, 1, 1],
        header=dict(
            values=list(data.columns),
            font=dict(size=18, color='white', family='ubuntu'),
            fill_color='#264653',
            align=['left', 'center'],
            height=60
        ),
        cells=dict(
            values=[data[K].tolist() for K in data.columns],
            font=dict(size=12, color='black'),
            font_size=12,
            font_color=['black', 'black', indicator],
            fill_color='#f0efeb',
            height=40
        )
    )]
    )
    fig.update_layout(margin=dict(l=30, r=30, b=10, t=80), height=350,
                      title=table_title)
    return fig


def format_hover_layout(fig):
    fig = fig.update_layout(
        height=400,
        hovermode="x unified",
        hoverlabel=dict(bgcolor="white", font_color="black",
                        font_size=12, font_family="Rockwell"))
    return fig
