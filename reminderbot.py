import praw
import pickle
import time
import re
from datetime import datetime, timedelta

# Initialize the Reddit instance with your bot's credentials
REDDIT_CLIENT_ID = "id_goes_here"
REDDIT_SECRET = "secret_goes_here"
REDDIT_USER_AGENT = "HelperFlairBot by ChatGPT and /u/apinanaivot"
REDDIT_USERNAME = "username_goes_here"
REDDIT_PASSWORD = "password_goes_here"

reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_SECRET,
    user_agent=REDDIT_USER_AGENT,
    username=REDDIT_USERNAME,
    password=REDDIT_PASSWORD,
)

# Load processed posts from file or create an empty set
try:
    with open("processed_posts.pickle", "rb") as f:
        processed_posts = pickle.load(f)
except FileNotFoundError:
    processed_posts = set()

def save_processed_posts():
    with open("processed_posts.pickle", "wb") as f:
        pickle.dump(processed_posts, f)

# Function to check if a post should be reminded
def should_remind(post):
    if post.link_flair_text == "Help!":
        post_age = datetime.utcnow() - datetime.utcfromtimestamp(post.created_utc)
        if post_age > timedelta(days=1):
            return True
    return False

# Function to send a reminder PM
def send_reminder(post):
    reminder_subject = "Just checking in: Has your /r/Photoshop question been answered? Mark it as solved!"
    reminder_text = (
        f"Hello {post.author.name}, it's been over 24 hours and it seems that your /r/Photoshop post titled "
        f"[{post.title}](https://www.reddit.com{post.permalink}) hasn't been marked as solved yet.\n\n"
        "If someone has helped you, please reply to their comment with "
        "'**Solved!**' to reward them with a helper point and mark the post as solved! If you already have thanked someone for their help, you can also simply edit that comment with the text 'Solved!'\n\n"
        "Thank you for keeping the community organized!"
    )

    while True:
        try:
            post.author.message(reminder_subject, reminder_text)
            print(f"Sent reminder to {post.author.name} for post: {post.id}")
            processed_posts.add(post.id)
            save_processed_posts()
            time.sleep(2)  # Add a 2-second delay after a successful message
            break
        except praw.exceptions.RedditAPIException as e:
            if "RATELIMIT" in str(e):
                wait_time = int(re.search(r"\d+", str(e)).group())  # Extract wait time using regex
                wait_time_seconds = wait_time * 60  # Convert wait time to seconds
                print(f"Rate limit hit. Waiting for {wait_time} minutes.")
                time.sleep(wait_time)
            else:
                raise

# Main function to search for posts that need reminders
def main():
    subreddit = reddit.subreddit("photoshop")
    for post in subreddit.new(limit=80):
        if post.id not in processed_posts and should_remind(post):
            send_reminder(post)
            processed_posts.add(post.id)

    # Save processed posts to file
    with open("processed_posts.pickle", "wb") as f:
        pickle.dump(processed_posts, f)

if __name__ == "__main__":
    main()
