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
    data = []
    table = soup.find('table')
    for row in table.find_all('tr')[1:]:  # Skip the header row
        cells = row.find_all('td')  # Find all <td> elements within the row
        if len(cells) == 4:  # Ensure there are at least 4 columns as per your example
            date = cells[0].text.strip()
            event = f"<h4>{cells[1].text.strip()}</h4>"
            location = cells[2].text.strip()
            # The image URL is in the fourth <td> (index 3)
            img_tag = cells[3].find('img')
            img = "<img src='./' width='30' height='30' style='vertical-align:middle;'>"
            if img_tag and 'src' in img_tag.attrs:
                img_url = img_tag['src']
                if not img_url.startswith('http'):
                    img_url = 'https://www.controlrisks.com' + img_url  # Complete the URL if needed
                # Combine location and image tag in HTML format
                img = f"<img src='{img_url}' width='30' height='30' style='vertical-align:middle;'>"
            else:
                location_with_img = location  # No image found, use location text only

            data.append([date, event, location, img])
        elif len(cells) == 1:  # Info row, add to the previous row's event
            info = cells[0].text.strip()
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
    df = create_dataframe(data, ['Date', 'Event', 'Location', ' '])
    return df
