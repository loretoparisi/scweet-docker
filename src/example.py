from Scweet.scweet import scrap
from Scweet.user import get_user_information, get_users_following, get_users_followers

# scrape top tweets with the words 'covid','covid19' in proximity and without replies. ",
# the process is slower as the interval is smaller (choose an interval that can divide the period of time betwee, start and max date) ",
data = scrap(words=['covid','covid19'], 
    start_date="2020-04-01", 
    max_date="2020-04-15", 
    from_account = None,
    interval=1, 
    headless=True, 
    display_type="Top", 
    save_images=False,
    resume=False, 
    filter_replies=True, 
    proximity=True,
    save_dir="/root/twitter")