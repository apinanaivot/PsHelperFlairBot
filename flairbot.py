import os
import praw
from praw.models import Message, MoreComments
import time
import pickle

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

#The subreddit the bot operates in
subreddit = reddit.subreddit("photoshop")

#These users cannot get helper points
BLACKLISTED_USERNAMES = ["automoderator"]



def save_processed_comments(processed_comments):
    with open("processed_comments.pickle", "wb") as f:
        pickle.dump(processed_comments, f)

def load_processed_comments():
    try:
        with open("processed_comments.pickle", "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return set()

def flatten_comments(comments):
    flattened_comments = []
    for comment in comments:
        if isinstance(comment, MoreComments):
            flattened_comments.extend(flatten_comments(comment.comments()))
        else:
            flattened_comments.append(comment)
    return flattened_comments

def get_helper_points(flair_text):
    if flair_text is None:
        return 0

    parts = flair_text.split("|")
    for part in parts:
        if "helper points" in part:
            return int(part.strip().split(" ")[0])
    return 0

def remove_helper_points(flair_text):
    if flair_text is None:
        return ''

    parts = flair_text.split("|")
    remaining_flair_parts = [part for part in parts if "helper points" not in part]
    return "|".join(remaining_flair_parts).strip()

def update_flair(user, new_points, old_flair):
    old_flair_without_helper_points = remove_helper_points(old_flair)
    updated_flair = f"{new_points} helper points"

    if old_flair_without_helper_points:
        updated_flair += f" | {old_flair_without_helper_points}"
    
    subreddit.flair.set(user, updated_flair)

def check_comments():
    print("Loading processed comments.")
    processed_comments = load_processed_comments()
    bot_username = REDDIT_USERNAME.lower()
    print("Iterating over new posts. (this can take a while)")
    for post in subreddit.new(limit=250):
        if post.link_flair_text is not None and post.link_flair_text in ("Solved"):
            all_comments = flatten_comments(post.comments.list())  # Get all comments in the thread
            
            for comment in all_comments:
                if isinstance(comment, Message) or comment.id in processed_comments:
                    continue

                all_replies = flatten_comments(comment.replies)  # Check all replies of each comment

                for reply in all_replies:
                    if reply.author == post.author and "solved!" in reply.body.lower():
                        print(f"Awarding helper point for comment {comment.id}.")
                        helper = comment.author

                        # Skip if the helper is the original poster or in the blacklist
                        if helper == post.author or helper.name.lower() in BLACKLISTED_USERNAMES:
                            continue

                        old_flair = next(subreddit.flair(helper))["flair_text"]
                        new_points = get_helper_points(old_flair) + 1
                        update_flair(helper, new_points, old_flair)
                        # Leave a comment to indicate that the helper point has been awarded
                        reply.reply(f"Helper point awarded to /u/{helper.name}!\n\n{helper.name} has {new_points} helper points now.")
                        # Mark the comment and reply as processed
                        processed_comments.add(comment.id)
                        processed_comments.add(reply.id)
                        save_processed_comments(processed_comments)

def log_error(error_message):
    with open('error_log.txt', 'a') as log_file:
        log_file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {error_message}\n")


if __name__ == "__main__":
    while True:
        try:
            print(f"Starting up a check.")
            check_comments()
            wait_time = 900  # Wait for 15 minutes before checking again
            print(f"Finished checking comments. Waiting for {wait_time // 60} minutes before checking again.")
            time.sleep(wait_time)
        except Exception as e:
            error_message = f"An error occurred: {e}"
            print(error_message)
            log_error(error_message)
            # Optional: Add a short wait time to prevent the script from entering an error loop.
            time.sleep(60)
        
