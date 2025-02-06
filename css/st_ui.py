"""
custom CSS for streamlit widgets
"""


st_ui_css = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    html, body, [class*="st-"] {
        font-family: 'Inter', sans-serif;
    }
    .stMetric {
       background-color: #dbebe8;
       # border: 1px solid rgba(28, 131, 225, 0.5);
       padding: 5% 5% 5% 10%;
       border-radius: 10px;
       color: rgb(30, 103, 119);
       overflow-wrap: break-word;
       height: 120px;
    }
    .main-svg{
        border-radius:20px;
        background: transparent;
    }
    
    #MainMenu {visibility: hidden;}
    
    footer {visibility: hidden;}
    
    header {visibility: hidden; height:0;}
    
    # .js-plotly-plot{
    #     margin: 40px;
    #     border-radius: 100px;
    # }
    
    .scrollbar-slider {
        display: none;
    }
    
    .scrollbar-capture-zone {
        display: none;
    }
    
    .block-container {
      margin-top: 25px;
      padding-top: 0;
    }
    table {
        width: 100%;
        margin-top: 1rem;
        border-collapse: collapse;
        border-spacing: 0;
        cell-spacing:0;
        cell-padding:0;
    }
    
    thead {
        background-color: #2b3d51;
        color: #ffffff;
        height: 5rem;
        font-size: 1.5rem;
    }
    
    th, td {
        padding: 15px;
        border-left: none; /* Remove left border */
        border-right: none; /* Remove right border */
        border: 0;
    }
    
    td {
        background: #f3f3f3;
        border-collapse:collapse;
        color: #2b3d51;
    }
    
    tr {
        border-top: none;
        border-bottom: none;
    }
    
    th:last-child, td:last-child {
        border-right: none;
    }
    
    th:first-child, td:first-child {
        border-left: none;
    }
</style>
"""

plotly_svg_css_1="""
<style>
    .stPlotlyChart {
         outline: none;
         border-radius: 2px;
         background: transparent;
         box-shadow: none;
         padding: 0;
    }
</style>
"""


plotly_svg_css_2="""
<style>
    .stPlotlyChart {
         outline: 5px solid white;
         border-radius: 10px;
         background: transparent;
         box-shadow: 0 4px 8px 0 rgba(0, 0, 0, 0.20), 0 6px 20px 0 rgba(0, 0, 0, 0.30);
         padding: 0;
    }
</style>
"""
