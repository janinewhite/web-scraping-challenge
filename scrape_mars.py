# Dependencies
from splinter import Browser
from bs4 import BeautifulSoup
import requests
import pymongo
import pandas as pd
from datetime import datetime
import config as cfg
import tweepy as tw
import json

# Constants
mars_sites = [{"Name":"NASA Mars Explorer News",
               "URL":"https://mars.nasa.gov/news",
               "Type":"News",
               "Link Stem":"https://mars.nasa.gov"
              },
              {"Name":"JPL Mars Images",
               "URL":"https://www.jpl.nasa.gov/spaceimages/?search=&category=Mars",
               "Type":"Featured Image",
               "Link Stem":"https://www.jpl.nasa.gov"
              },
              {"Name":"Mars Weather",
               "URL":"https://twitter.com/marswxreport?lang=en",
               "Type":"Weather",
               "Account":"MarsWxReport"
              },
              {"Name":"Mars Facts",
               "URL":"https://space-facts.com/mars/",
               "Type":"Facts"
              },
              {"Name":"Mars Hemispheres",
               "URL":"https://astrogeology.usgs.gov/search/results?q=hemisphere+enhanced&k1=target&v1=Mars",
               "Type":"Hemispheres",
               "Link Stem":"https://astrogeology.usgs.gov"
              }]

def get_page(url):
    executable_path = {"executable_path": cfg.chromedriver_path}
    browser = Browser("chrome", **executable_path, headless=False)
    browser.visit(url)
    html = browser.html
    soup = BeautifulSoup(html, "html.parser")
    browser.quit()
    return soup

def scrape_news(site):
    print("News Article")
    print(site["Name"])
    print("____________")
    executable_path = {"executable_path": cfg.chromedriver_path}
    browser = Browser("chrome", **executable_path, headless=False)
    browser.visit(site['URL'])
    html = browser.html
    news_soup = BeautifulSoup(html, "html.parser")
    browser.quit()
    #news_soup = get_page(site['URL'])
    latest_date = datetime(2000, 1, 1, 0, 0)
    article_url = ""
    article_title = ""
    article_description = ""
    articles = news_soup.find_all("div",class_ = "list_text")
    for article in articles:
        date_text = article.find("div",class_="list_date").text
        article_date = datetime.strptime(date_text,'%B %d, %Y')
        if article_date > latest_date:
            latest_date = article_date
            print(article_date)
            article_link = article.find("div",class_="content_title")
            article_url = f"{site['Link Stem']}{article_link.a['href']}"
            print(article_url)
            article_title = article_link.a.text.replace('\n','').strip()
            print(article_title)
            description = article.find("div", class_ = "article_teaser_body")
            article_description = description.text.strip()
            print(article_description)
    print("____________")
    detail = {}
    detail["Detail"] = article_title
    detail["Detail URL"] = article_url
    detail["Detail Description"] = article_description
    return detail

def scrape_featured_image(site):
    print("Featured Image")
    print("____________")
    featured_soup = get_page(site['URL'])
    article = {}
    image = featured_soup.find("article",class_="carousel_item")
    print(image["alt"])
    image_style = image["style"]
    image_link = image_style[image_style.find("'")+1:]
    image_link = image_link[:image_link.find("'")]
    print(image_link)
    article["Detail"] = image["alt"]
    article["Detail URL"] = f"{site['Link Stem']}{image_link}"
    article["Detail Description"] = "Jet Propulsion Laboratory Featured Image"
    return article

def get_Twitter_API():
    consumer_key = cfg.Twitter_Consumer_API_Key
    consumer_secret = cfg.Twitter_Consumer_Secret_API_Key
    access_token = cfg.Twitter_Access_Token
    access_token_secret = cfg.Twitter_Access_Token_Secret
    auth = tw.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret) 
    api = tw.API(auth)
    return api

def scrape_weather(site):
    print("Mars Weather")
    print("____________")
    # Use API to get latest Mars Weather tweet
    api = get_Twitter_API()
    twitter_account = site["Account"]
    status = api.user_timeline(twitter_account,count=1,page=1)
    #json_str = json.dumps(status[0]._json)
    #parsed = json.loads(json_str)
    #print(json.dumps(parsed, indent=4, sort_keys=True))
    entities = status[0].entities
    urls = dict(entities["urls"][0])
    last_tweet_url = ""
    for key in urls.keys():
        if key == "expanded_url":
            last_tweet_url = urls[key]
    print(last_tweet_url)
    # Scrape text of latest tweet
    weather_soup = get_page(last_tweet_url)
    tweet = weather_soup.find("div",class_="js-tweet-text-container")
    tweet_text = tweet.p.text.replace('\n','').strip()
    tweet_text = tweet_text[:(tweet_text.find("hPapic.twitter.com")-1)]
    print(tweet_text)
    article = {}
    article["Detail"] = tweet_text
    article["Detail URL"] = last_tweet_url
    article["Detail Description"] = "Mars Weather Tweet"
    return article

def scrape_facts(site):
    print("Mars Facts")
    print("____________")
    facts_soup = get_page(site['URL'])
    table = facts_soup.find("table",class_="tablepress tablepress-id-p-mars")
    table_body = table.tbody
    columns = table_body.find_all("td")
    descriptions = []
    values = []
    col_num = 0
    for column in columns:
        column_text = column.text
        if (col_num % 2) == 0:
            column_text = column_text[0:(len(column_text)-1)]
            descriptions.append(column_text)
        else:
            values.append(column_text)
        col_num += 1
    facts = pd.DataFrame()
    facts["Description"] = descriptions
    facts["Values"] = values
    facts = facts.set_index("Description")
    print(facts)
    facts_table = facts.to_dict()
    article = {}
    article["Detail"] = facts_table["Values"]
    article["Detail URL"] = site['URL']
    article["Detail Description"] = "Mars Facts"
    return article

def scrape_hemispheres(site):
    print("Mars Hemispheres")
    print("____________")
    hemispheres_soup = get_page(site['URL'])
    items = hemispheres_soup.find_all("div",class_="item")
    link_stem = site["Link Stem"]
    hemispheres = []
    for item in items:
        hemisphere = {}
        hemisphere["Name"] = item.img["alt"].split(" ")[0]
        hemisphere_page = f"{link_stem}{item.a['href']}"
        hemisphere["Page"] = hemisphere_page
        hemisphere_soup = get_page(hemisphere_page)
        hemisphere_image = hemisphere_soup.find("img",class_="wide-image")
        hemisphere["Image"] = f"{link_stem}{hemisphere_image['src']}"
        hemispheres.append(hemisphere)
    article = {}
    article["Detail"] = hemispheres
    article["Detail URL"] = site["URL"]
    article["Detail Description"] = "Mars Hemispheres"
    return article

def get_post(site):
    post = {}
    post.update({"Site":site["Name"]})
    url = site["URL"]
    post["Site URL"] = url
    site_type = site["Type"]
    post["Site Type"] = site_type
    details = {}
    if site['Type'] == "News":
        details = scrape_news(site)
    elif site['Type'] == "Featured Image":
        details = scrape_featured_image(site)
    elif site['Type'] == "Weather":
        details = scrape_weather(site)
    elif site['Type']=="Facts":
        details = scrape_facts(site)
    else:
        details = scrape_hemispheres(site)
    print(f"{site['Name']} Details:")
    print(details)
    print()
    post["Detail"] = details["Detail"]
    post["Detail URL"] = details["Detail URL"]
    post["Detail Description"] = details["Detail Description"]
    return post
          
def scrape_sites():
    sites = []
    for site in mars_sites:
        post = get_post(site)
        sites.append(post)
    return sites

def scrape():
    # Insert Mars site into MongoDB
    conn = 'mongodb://localhost:27017'
    client = pymongo.MongoClient(conn)
    db = client.mars_db
    db.mars.drop()
    posts = scrape_sites()
    x = db.mars.insert_many(posts)
    print(x.inserted_ids)
    # Verify insertion
    items = db.mars.find()
    for item in items:
        print(item['Site'])


