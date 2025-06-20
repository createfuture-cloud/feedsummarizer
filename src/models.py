from datetime import datetime

from pydantic import BaseModel, Field


class MessageCategoryEntry(BaseModel):
    headline: str = Field(
        description="Blog-post headline/title/summary for this update. This can be up to two sentences long and should be reasonably descriptive."
    )
    link: str = Field(description="Link to the source for this update")


class MessageCategory(BaseModel):
    emoji: str = Field(description="Slack-Coded Emoji for this category")
    title: str = Field(description="Title for this category of updates")
    entries: list[MessageCategoryEntry] = Field(
        description="Individual entries within this category"
    )


class SlackMessage(BaseModel):
    categories: list[MessageCategory]


class FeedItem(BaseModel):
    title: str
    description: str
    pub_date: str
    link: str

    @property
    def timestamp(self):
        parsed = datetime.strptime(self.pub_date, "%a, %d %b %Y %H:%M:%S %Z")
        return int(parsed.timestamp())
