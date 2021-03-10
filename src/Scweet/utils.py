from io import StringIO, BytesIO
import os
import re
from time import sleep
import random
import chromedriver_autoinstaller
from selenium.common.exceptions import NoSuchElementException
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import datetime
import pandas as pd
import platform
from selenium.webdriver.common.keys import Keys
# import pathlib

from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from . import const
import urllib

# current_dir = pathlib.Path(__file__).parent.absolute()

def get_data(card, save_images = False, save_dir = None):
    """Extract data from tweet card"""
    image_links = []

    try:
        username = card.find_element_by_xpath('.//span').text
    except:
        return

    try:
        handle = card.find_element_by_xpath('.//span[contains(text(), "@")]').text
    except:
        return

    try:
        postdate = card.find_element_by_xpath('.//time').get_attribute('datetime')
    except:
        return

    try:
        text = card.find_element_by_xpath('.//div[2]/div[2]/div[1]').text
    except:
        text = ""

    try:
        embedded = card.find_element_by_xpath('.//div[2]/div[2]/div[2]').text
    except:
        embedded = ""

    #text = comment + embedded

    try:
        reply_cnt = card.find_element_by_xpath('.//div[@data-testid="reply"]').text
    except:
        reply_cnt = 0

    try:
        retweet_cnt = card.find_element_by_xpath('.//div[@data-testid="retweet"]').text
    except:
        retweet_cnt = 0

    try:
        like_cnt = card.find_element_by_xpath('.//div[@data-testid="like"]').text
    except:
        like_cnt = 0

    try:
        elements = card.find_elements_by_xpath('.//div[2]/div[2]//img[contains(@src, "https://pbs.twimg.com/")]')
        for element in elements:
        	image_links.append(element.get_attribute('src'))
    except:
        image_links = []

    #if save_images == True:
    #	for image_url in image_links:
    #		save_image(image_url, image_url, save_dir)
    # handle promoted tweets

    try:
        promoted = card.find_element_by_xpath('.//div[2]/div[2]/[last()]//span').text == "Promoted"
    except:
        promoted = False
    if promoted:
        return

    # get a string of all emojis contained in the tweet
    try:
        emoji_tags = card.find_elements_by_xpath('.//img[contains(@src, "emoji")]')
    except:
        return
    emoji_list = []
    for tag in emoji_tags:
        try:
            filename = tag.get_attribute('src')
            emoji = chr(int(re.search(r'svg\/([a-z0-9]+)\.svg', filename).group(1), base=16))
        except AttributeError:
            continue
        if emoji:
            emoji_list.append(emoji)
    emojis = ' '.join(emoji_list)

    # tweet url
    try:
        element = card.find_element_by_xpath('.//a[contains(@href, "/status/")]')
        tweet_url = element.get_attribute('href')
    except:
        return

    tweet = (username, handle, postdate, text, embedded, emojis, reply_cnt, retweet_cnt, like_cnt, image_links, tweet_url)
    return tweet



def init_driver(headless=True, proxy=None, show_images=False):
    """ initiate a chromedriver instance """

    # create instance of web driver
    chromedriver_path = chromedriver_autoinstaller.install()
    options = Options()
    if headless is True:

        print("Scraping on headless mode.")
        options.add_argument('--disable-gpu')
        options.headless = True
    else:
        options.headless = False
    options.add_argument('log-level=3')
    if proxy is not None:
        options.add_argument('--proxy-server=%s' % proxy)
    if show_images == False:
    	prefs = {"profile.managed_default_content_settings.images": 2}
    	options.add_experimental_option("prefs", prefs)

    # LP: fixed the unknown error: DevToolsActivePort file doesn't exist
    options.add_argument('--no-sandbox')
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--profile-directory=Default')
    options.add_argument('--user-data-dir=./.config/google-chrome')

    driver = webdriver.Chrome(options=options, executable_path=chromedriver_path)
    driver.set_page_load_timeout(100)
    
    return driver


def log_search_page(driver, start_date, end_date, lang, display_type, words, to_account, from_account, hashtag, filter_replies, proximity):
    """ Search for this query between start_date and end_date"""

    # format the <from_account>, <to_account> and <hash_tags>
    from_account = "(from%3A" + from_account + ")%20" if from_account is not None else ""
    to_account = "(to%3A" + to_account + ")%20" if to_account is not None else ""
    hash_tags = "(%23" + hashtag + ")%20" if hashtag is not None else ""

    if words is not None:
        if len(words)==1:
            words = "(" +  str(''.join(words)) + ")%20"
        else :
            words = "(" + str('%20OR%20'.join(words)) + ")%20"
    else:
        words = ""

    if lang is not None:
        lang = 'lang%3A' + lang
    else:
        lang = ""

    end_date = "until%3A" + end_date + "%20"
    start_date = "since%3A" + start_date + "%20"

    if display_type == "Latest" or display_type == "latest":
    	display_type = "&f=live"
    elif display_type == "Image" or display_type == "image":
    	display_type = "&f=image"
    else:
    	display_type = ""

    # filter replies 
    if filter_replies == True:
        filter_replies = "%20-filter%3Areplies"
    else :
        filter_replies = ""
    # proximity
    if proximity == True:
        proximity = "&lf=on" # at the end
    else : 
        proximity = ""

    path = 'https://twitter.com/search?q='+words+from_account+to_account+hash_tags+end_date+start_date+lang+filter_replies+'&src=typed_query'+display_type+proximity
    driver.get(path)
    return path


def get_last_date_from_csv(path):
    df = pd.read_csv(path)
    return datetime.datetime.strftime(max(pd.to_datetime(df["Timestamp"])), '%Y-%m-%dT%H:%M:%S.000Z')


def log_in(driver, timeout=10):
    username = const.USERNAME
    password = const.PASSWORD

    driver.get('https://www.twitter.com/login')
    username_xpath = '//input[@name="session[username_or_email]"]'
    password_xpath = '//input[@name="session[password]"]'

    username_el = WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.XPATH, username_xpath)))
    password_el = WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.XPATH, password_xpath)))

    username_el.send_keys(username)
    password_el.send_keys(password)
    password_el.send_keys(Keys.RETURN)


def keep_scroling(driver, data, writer, tweet_ids, scrolling, tweet_parsed, limit, scroll, last_position, save_dir="outputs", save_images = False):
    """ scrolling function for tweets crawling"""

    save_images_dir = os.path.join(save_dir, "images")
    if save_images == True:
    	if not os.path.exists(save_images_dir):
    		os.mkdir(save_images_dir)

    while scrolling and tweet_parsed < limit:
        sleep(random.uniform(0.5, 1.5))
        # get the card of tweets
        page_cards = driver.find_elements_by_xpath('//div[@data-testid="tweet"]')
        for card in page_cards:
            tweet = get_data(card, save_images, save_images_dir)
            if tweet:
                # check if the tweet is unique
                tweet_id = ''.join(tweet[:-2])
                if tweet_id not in tweet_ids:
                    tweet_ids.add(tweet_id)
                    data.append(tweet)
                    last_date = str(tweet[2])
                    print("Tweet made at: " + str(last_date) + " is found.")
                    writer.writerow(tweet)
                    tweet_parsed += 1
                    if tweet_parsed >= limit:
                        break
        scroll_attempt = 0
        while tweet_parsed < limit:
            # check scroll position
            scroll += 1
            print("scroll ", scroll)
            sleep(random.uniform(0.5, 1.5))
            driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
            curr_position = driver.execute_script("return window.pageYOffset;")
            if last_position == curr_position:
                scroll_attempt += 1
                # end of scroll region
                if scroll_attempt >= 2:
                    scrolling = False
                    break
                else:
                    sleep(random.uniform(0.5, 1.5))  # attempt another scroll
            else:
                last_position = curr_position
                break
    return driver, data, writer, tweet_ids, scrolling, tweet_parsed, scroll, last_position


def get_users_follow(users, headless, follow=None, verbose=1, wait=2):
	""" get the following or followers of a list of users """

	# initiate the driver
	driver = init_driver(headless=headless)
	sleep(wait)
	# log in (the .env file should contain the username and password)
	log_in(driver)
	sleep(wait)
	# followers and following dict of each user
	follows_users = {}

	for user in users:
	    # log user page
	    print("Crawling @" + user + " "+ follow)
	    driver.get('https://twitter.com/' + user)
	    sleep(random.uniform(wait-0.5, wait+0.5))
	    # find the following or followers button
	    driver.find_element_by_xpath('//a[contains(@href,"/' + follow + '")]/span[1]/span[1]').click()
	    sleep(random.uniform(wait-0.5, wait+0.5))
	    # if the log in fails, find the new log in button and log in again.
	    if check_exists_by_link_text("Log in", driver):
	        login = driver.find_element_by_link_text("Log in")
	        sleep(random.uniform(wait-0.5, wait+0.5))
	        driver.execute_script("arguments[0].click();", login)
	        sleep(random.uniform(wait-0.5, wait+0.5))
	        driver.get('https://twitter.com/' + user)
	        sleep(random.uniform(wait-0.5, wait+0.5))
	        driver.find_element_by_xpath('//a[contains(@href,"/' + follow + '")]/span[1]/span[1]').click()
	        sleep(random.uniform(wait-0.5, wait+0.5))
	    # check if we must keep scrolling
	    scrolling = True
	    last_position = driver.execute_script("return window.pageYOffset;")
	    follows_elem = []
	    follow_ids = set()

	    while scrolling:
	        # get the card of following or followers
	        page_cards = driver.find_elements_by_xpath('//div[contains(@data-testid,"UserCell")]')
	        for card in page_cards:
	        	# get the following or followers element
	            element = card.find_element_by_xpath('.//div[1]/div[1]/div[1]//a[1]')
	            follow_elem = element.get_attribute('href')
	            # append to the list
	            follow_id = str(follow_elem)
	            follow_elem = '@' + str(follow_elem).split('/')[-1]
	            if follow_id not in follow_ids:
	            	follow_ids.add(follow_id)
	            	follows_elem.append(follow_elem)
	            if verbose:
	                print(follow_elem)
	        print("Found " + str(len(follows_elem)) + " " + follow)
	        scroll_attempt = 0
	        while True:
	            sleep(random.uniform(wait-0.5, wait+0.5))
	            driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
	            sleep(random.uniform(wait-0.5, wait+0.5))
	            curr_position = driver.execute_script("return window.pageYOffset;")
	            if last_position == curr_position:
	                scroll_attempt += 1

	                # end of scroll region
	                if scroll_attempt >= 3:
	                    scrolling = False
	                    break
	                    #return follows_elem
	                else:
	                    sleep(random.uniform(wait-0.5, wait+0.5))  # attempt another scroll
	            else:
	                last_position = curr_position
	                break

	    follows_users[user] = follows_elem

	return follows_users



def check_exists_by_link_text(text, driver):
    try:
        driver.find_element_by_link_text(text)
    except NoSuchElementException:
        return False
    return True


def dowload_images(urls, save_dir):

	for i, url_v in enumerate(urls):
		for j, url in enumerate(url_v):
			urllib.request.urlretrieve(url, save_dir + '/' + str(i+1) + '_' + str(j+1) + ".jpg")

