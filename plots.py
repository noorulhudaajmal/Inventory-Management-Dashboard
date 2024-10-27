import pandas as pd
import datetime
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

colors = ["#264653", "#2a9d8f", "#e9c46a", "#f4a261", "#e76f51", "#84a59d", "#006d77",
          "#f6bd60", "#90be6d", "#577590", "#e07a5f", "#81b29a", "#f2cc8f", "#0081a7"]

months_list = ['January', 'February', 'March', 'April', 'May', 'June',
               'July', 'August', 'September', 'October', 'November', 'December']


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
        fig.add_trace(
            go.Bar(x=data.index, y=data[size], name=size, marker=dict(color=colors[i])))
        i += 1

    fig.update_layout(barmode='group', xaxis_title='Depot', yaxis_title='# Units Sold',
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
