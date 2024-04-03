import pandas as pd
import datetime
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

colors = ["#264653", "#2a9d8f", "#e9c46a", "#f4a261", "#e76f51", "#84a59d", "#006d77",
          "#f6bd60", "#90be6d", "#577590", "#e07a5f", "#81b29a", "#f2cc8f", "#0081a7"]

months_list = ['January', 'February', 'March', 'April', 'May', 'June',
               'July', 'August', 'September', 'October', 'November', 'December']


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

    heatmap_data = df_agg_sorted.pivot("Month", "Year", "MARKET_PRICE_USD")
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


def available_for_sale_plot(data):
    fig = go.Figure()
    i = 0
    for size in data.columns:
        fig.add_trace(
            go.Bar(x=data.index, y=data[size], name=size, marker=dict(color=colors[i])))
        i += 1

    fig.update_layout(barmode='group', xaxis_title='Depot', yaxis_title='Units Available for Sale',
                      title='INVENTORY AVAILABLE FOR SALE',
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
               marker=dict(color="#264653"))
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
    fig = go.Figure()
    ind = 0
    for loc in data["SALES_LOCATION_NAME"].unique():
        filtered_df1 = data[data["SALES_LOCATION_NAME"] == loc]
        fig.add_trace(
            go.Scatter(
                x=filtered_df1["WEEK_TO_DISPLAY"], y=filtered_df1["MEAN_PRICE_PER_CONTAINER"],
                mode="lines+markers", name=loc, line=dict(color=colors[ind]), marker=dict(color=colors[ind])
            )
        )
        ind += 1
    fig.update_layout(
        title='Container Prices w.r.t Location overtime',
        xaxis_title='Date',
        yaxis_title="Container Prices",
        legend_title="Sales Location")
    fig = format_hover_layout(fig)
    return fig


def format_hover_layout(fig):
    fig = fig.update_layout(
        hovermode="x unified",
        hoverlabel=dict(bgcolor="white", font_color="black",
                        font_size=12, font_family="Rockwell"))
    return fig

