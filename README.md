# UdemyFreeBot

A Discord bot that automatically posts free Udemy courses from DiscUdemy.

## Features
- Daily updates of free courses
- Supports categories (e.g., Python, WordPress)
- `/free` command to fetch manually
- 24/7 deployment on cloud (e.g., Railway)

## Requirements
- Python 3.10+
- Discord bot token
- Discord channel ID

## Setup
1. Install dependencies:
pip install -r requirements.txt

2.Create .env:
 - DISCORD_TOKEN=your_bot_token
 - CHANNEL_ID=your_channel_id
 - CATEGORY_SLUG=python
 - PAGES_TO_SCRAPE=1

3.Run locally:
python bot.py

