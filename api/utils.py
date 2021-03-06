import requests

from . import app_settings

FB_GRAPH_URL = "https://graph.facebook.com/v10.0"


def get_facebook_posts():
    fields = "full_picture,message,created_time,permalink_url,from"
    url = f"{FB_GRAPH_URL}/{app_settings.FB_PAGE_ID}/feed?fields={fields}"
    url += f"&access_token={app_settings.FB_PAGE_TOKEN}"
    response = requests.get(url)
    if response.status_code != 200:
        return []
    resp_data = response.json()
    posts = []
    for post in resp_data.get("data"):
        from_data = post.get("from")
        posts.append(
            {
                "from_name": from_data.get("name"),
                "message": post.get("message"),
                "image": post.get("full_picture"),
                "permalink": post.get("permalink_url"),
                "created_at": post.get("created_time"),
            }
        )
    return posts
