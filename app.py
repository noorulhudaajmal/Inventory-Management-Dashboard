import streamlit as st
from streamlit_gsheets import GSheetsConnection
from streamlit_option_menu import option_menu

from css.st_ui import st_ui_css
from utils import load_data
from views import overview_page, commodities_page, trading_prices_page, calendar_page, news_page, sales_analytics_page


# Page Config
st.set_page_config(page_title="Inventory Insights", page_icon="📊", layout="wide")
st.markdown(st_ui_css, unsafe_allow_html=True)

# Update the GSheets connection
conn = st.connection("gsheets", type=GSheetsConnection)
conn_pricing = st.connection("pricing_data", type=GSheetsConnection)

with st.sidebar:
    st.image("assets/logo.png", width=200, channels="RGB")
    st.write("# ")
    st.write("---")

# data
inv_datasheet, price_data, df_trading = load_data(conn, conn_pricing)

# dashboard tabs
tabs_to_display = ["Overview","Sales Analytics", "Trading Prices", "Macro", "Calendar", "News"]
icons = ["house-door", "bar-chart-line", "graph-up", "bar-chart", "calendar-check", "newspaper"]

if inv_datasheet is not None:
    # Menu Pane
    menu = option_menu(menu_title=None, options=tabs_to_display, orientation="horizontal", icons=icons)

    if menu == "Overview":
        overview_page(price_data)
    if menu == "Sales Analytics":
        sales_analytics_page(data=inv_datasheet)
    if menu == "Trading Prices":
        trading_prices_page(df_trading=df_trading)
    if menu == "Macro":
        commodities_page(df_trading=df_trading)
    if menu == "Calendar":
        calendar_page()
    if menu == "News":
        news_page()

else:
    st.error("Data not available.")


