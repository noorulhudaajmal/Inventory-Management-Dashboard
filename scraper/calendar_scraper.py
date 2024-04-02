import pandas as pd
from bs4 import BeautifulSoup
import requests


def fetch_page(url):
    """Fetch the content of a webpage."""
    response = requests.get(url)
    if response.status_code == 200:
        return response.content
    else:
        raise Exception(f"Failed to fetch page: {response.status_code}")


def parse_table(html_content):
    """Parse the table from the HTML content and return the data."""
    soup = BeautifulSoup(html_content, 'html.parser')
    table = soup.find("table")
    data = []
    for row in table.find_all('tr')[1:]:  # Skip the header row
        cols = row.find_all('td')
        if len(cols) == 4:  # Regular row with event details
            date = cols[0].text.strip()
            event = cols[1].text.strip()
            location = cols[2].text.strip()
            data.append([date, event, location])
        elif len(cols) == 1:  # Info row, add to the previous row's event
            info = cols[0].text.strip()
            if data:
                data[-1][1] += " " + info
    return data


def create_dataframe(data, columns):
    """Create a DataFrame from the data."""
    return pd.DataFrame(data, columns=columns)


def get_geopolitical_calendar():
    url = "https://www.controlrisks.com/our-thinking/geopolitical-calendar"
    html_content = fetch_page(url)
    data = parse_table(html_content)
    df = create_dataframe(data, ['Date', 'Event', 'Location'])
    return df
