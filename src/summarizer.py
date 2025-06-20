import os
from datetime import datetime, timedelta
from html.parser import HTMLParser
from io import StringIO

import requests
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities import parameters
from aws_lambda_powertools.utilities.typing import LambdaContext
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_aws import ChatBedrockConverse
from rss_parser import RSSParser
from slack_sdk.webhook import WebhookClient

from models import FeedItem, SlackMessage

# Configurable
MODEL = os.environ["BEDROCK_MODEL"]
MAXLEN_DESCRIPTION = int(os.environ.get("MAXLEN_DESCRIPTION", "2500"))
PARAM_SLACK_WEBHOOK = os.environ["PARAM_SLACK_WEBHOOK"]
USER_AGENT = os.environ.get("USER_AGENT", "feedsummarizer 0.1 +harry@reeder.dev")

# TODO: Make FEED_URL and SYSTEM_PROMPT configurable
FEED_URL = "https://aws.amazon.com/about-aws/whats-new/recent/feed/"
SYSTEM_PROMPT = """Using the following entries from the AWS "What's New" feed, create a once-per-week message to post to slack to keep people up to date with what they should know.

Ensure that anything which is in preview is clearly marked as such.

Categories should have relevant emoji, and individual entries should have a "Learn More" link to the article's page.
"""

LLM = ChatBedrockConverse(
    model=MODEL,
    temperature=0.5,
    max_tokens=None,
)

SLACK_WEBHOOK_URL = parameters.get_parameter(PARAM_SLACK_WEBHOOK, decrypt=True)

log = Logger()


# From: https://stackoverflow.com/a/925630
class MLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text = StringIO()

    def handle_data(self, d):
        self.text.write(d)

    def get_data(self):
        return self.text.getvalue()


def strip_tags(html: str) -> str:
    s = MLStripper()
    s.feed(html)
    return s.get_data()


def get_feed_entries(feed_url: str, since: int) -> list[FeedItem]:
    response = requests.get(feed_url, headers={"User-Agent": USER_AGENT})
    response_text = response.text
    log.debug(
        "got feed",
        extra={
            "feed_url": feed_url,
            "response": {
                "status_code": response.status_code,
                "headers": dict(response.headers),
            },
        },
    )
    feed = RSSParser.parse(response_text)

    items = [
        FeedItem(
            title=it.title.content,
            description=strip_tags(it.description.content)[:MAXLEN_DESCRIPTION],
            pub_date=it.pub_date.content,
            link=it.links[0].content,
        )
        for it in feed.channel.items
    ]

    items = [it for it in items if it.timestamp > since]
    oldest = min(items, key=lambda it: it.timestamp)

    log.debug(
        "filtered items",
        extra={
            "item_count": len(items),
            "maxlen_description": MAXLEN_DESCRIPTION,
            "oldest": oldest.pub_date,
        },
    )

    return items


def get_summary_message(feed_items: list[FeedItem]) -> SlackMessage:
    messages = [
        SystemMessage(SYSTEM_PROMPT),
        HumanMessage("\n".join([it.model_dump_json() for it in feed_items])),
    ]
    model = LLM.with_structured_output(SlackMessage)
    log.debug("invoking model", extra={"model": MODEL})
    response = model.invoke(messages)
    log.debug("got response")

    return response


def send_to_slack(message: SlackMessage):
    client = WebhookClient(SLACK_WEBHOOK_URL)

    for category in message.categories:
        slack_message = f"{category.emoji} *{category.title}*"
        for entry in category.entries:
            slack_message += f"\n • {entry.headline} - <{entry.link}|Learn More>"

        client.send(text=slack_message)


def main():
    if SLACK_WEBHOOK_URL == "not-set":
        raise ValueError(
            f"No Slack Webhook URL is currently set in SSM at {os.environ['PARAM_SLACK_WEBHOOK']}"
        )

    now = datetime.now()
    last_week = now - timedelta(weeks=1)

    entries = get_feed_entries(FEED_URL, since=int(last_week.timestamp()))
    message = get_summary_message(entries)
    send_to_slack(message)


@log.inject_lambda_context
def lambda_handler(event: dict, context: LambdaContext):
    main()


if __name__ == "__main__":
    main()
