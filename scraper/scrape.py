import requests
from bs4 import BeautifulSoup
import pandas as pd


def get_webdata(url):
    r = requests.get(url)
    soup = BeautifulSoup(r.content, 'lxml')
    return soup


def get_table(soup, table_id):
    table = soup.find("table", attrs={"id": table_id})
    return table


def get_table_data(table):
    columns = []
    data = []
    header_row = table.find('tr', class_='row-1')
    for th in header_row.find_all('th'):
        columns.append(th.text.strip())
    rows = table.find_all('tr')[1:]
    for row in rows:
        row_data = []
        for td in row.find_all('td'):
            row_data.append(td.text.strip())
        data.append(row_data)
    df = pd.DataFrame(data, columns=columns)
    return df


def preprocess_data(df):
    for i in df.columns:
        if "FT" in i:
            df[i] = df[i].str.replace(',', '').str.replace('$', '').astype(int)
    df["Port"] = df["Origin Country (Port/City)"].apply(lambda x:x.split(" (")[0])
    return df


def scrap_data(url):
    soup = get_webdata(url)
    table = get_table(soup, "tablepress-29")
    df = get_table_data(table)
    df = preprocess_data(df)
    return df

