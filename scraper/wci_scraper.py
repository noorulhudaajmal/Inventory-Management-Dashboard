import requests
from bs4 import BeautifulSoup
import pandas as pd

def fetch_html(url):
    """
    Fetch HTML content from the given URL.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.text
    else:
        raise Exception(f"Failed to fetch HTML. Status code: {response.status_code}")

def parse_table(html_content):
    """
    Parse the HTML content and extract the table data.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    table = soup.find('table', id='tablepress-384')

    if not table:
        raise Exception("Could not find the table with id 'tablepress-384'.")

    # Extract headers
    headers = [th.text.strip() for th in table.find('thead').find_all('th')]

    # Extract rows
    rows = []
    for row in table.find('tbody').find_all('tr'):
        cells = [cell.text.strip() for cell in row.find_all('td')]
        rows.append(cells)

    return headers, rows



def get_wci_data():
    url = "https://moverdb.com/container-shipping/"

    try:
        # Fetch HTML content
        html_content = fetch_html(url)

        # Parse HTML and extract table data
        headers, rows = parse_table(html_content)

        # Create DataFrame
        df = pd.DataFrame(rows, columns=headers)

        return df

    except Exception as e:
        print(f"An error occurred: {e}")
        return None