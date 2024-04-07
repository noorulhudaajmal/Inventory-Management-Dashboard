import requests
from bs4 import BeautifulSoup
import pandas as pd


def fetch_posts(url):
    r = requests.get(url)
    if r.status_code == 200:
        return r.content
    else:
        return None


def parse_posts(html_content):
    soup = BeautifulSoup(html_content, 'lxml')
    posts = soup.find_all("div", attrs={"class": 'tgme_widget_message_wrap js-widget_message_wrap'})
    return posts


def extract_post_info(posts):
    post_details = []
    for post in posts:
        # Basic post information
        text = post.find("div", class_="tgme_widget_message_text").text if post.find("div", class_="tgme_widget_message_text") else None
        date = post.find("time")["datetime"] if post.find("time") else None

        # Extracting telegram post ID
        telegram_post_id = None
        message_div = post.find("div", class_="tgme_widget_message")
        if message_div and "data-post" in message_div.attrs:
            telegram_post_id = message_div["data-post"]

        # Finding the main link (if any) in the post content
        link = None
        photo_wrap_link = post.find("a", class_="tgme_widget_message_photo_wrap")
        if photo_wrap_link:
            link = photo_wrap_link["href"]

        # Finding the "Read More" button link
        read_more_link = post.find("a", class_="tgme_widget_message_inline_button")
        if read_more_link:
            link = read_more_link["href"]  # This overrides the main link if both exist

        # Extracting image URL
        image_style = photo_wrap_link["style"] if photo_wrap_link else None
        image_url = image_style.split("url('")[1].split("')")[0] if image_style else None

        # Extracting height from svg element
        div_height = None
        svg_element = post.find("svg")
        if svg_element:
            div_height = int(svg_element.get("height")[:-2])

        post_details.append({"text": text, "date": date, "telegram_post_id": telegram_post_id,
                             "link": link, "image": image_url, "div_height": div_height})
    return post_details


def posts_to_dataframe(post_details):
    df = pd.DataFrame(post_details)
    return df


def extract_news():
    url = "https://t.me/s/PortPulse/3476"
    html_content = fetch_posts(url)
    df = pd.DataFrame()
    if html_content:
        posts = parse_posts(html_content)
        post_details = extract_post_info(posts)
        df = posts_to_dataframe(post_details)

        # Apply the function to update the div_height column
        df['div_height'] = df.apply(update_div_height, axis=1)
        df['div_height'] = df['div_height'].astype(int)

    return df


# Define a function to update div_height
def update_div_height(row):
    if row['image'] is None:
        return 11 * row['div_height']
    else:
        return 20 * row['div_height']