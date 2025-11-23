# bot.py
# Requirements:
# pip install discord.py requests beautifulsoup4 python-dotenv

import os
import time
import json
import asyncio
import requests
from bs4 import BeautifulSoup
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

# Load .env
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID") or 0)
CATEGORY_SLUG = os.getenv("CATEGORY_SLUG")
PAGES_TO_SCRAPE = int(os.getenv("PAGES_TO_SCRAPE") or 1)

# Discord intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

BASE = "https://www.discudemy.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
}

HISTORY_FILE = "sent.json"


# -----------------------------
# Load / Save history
# -----------------------------
def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []

    try:
        with open(HISTORY_FILE, "r", encoding="utf8") as f:
            return json.load(f)
    except:
        return []


def save_history(data):
    with open(HISTORY_FILE, "w", encoding="utf8") as f:
        json.dump(data, f, indent=2)


# -----------------------------
# Scraper Sync
# -----------------------------
def _scrape_category_sync(slug=None, pages=1, per_article_delay=0.25):
    results = []
    base_url = BASE if not slug else f"{BASE}/category/{slug}"
    seen_posts = set()

    for p in range(1, pages + 1):
        url = base_url if p == 1 else f"{base_url}/page/{p}/"

        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            r.raise_for_status()
        except Exception as e:
            print(f"[scraper] Failed to load {url}: {e}")
            continue

        soup = BeautifulSoup(r.text, "html.parser")
        anchors = soup.select("div.card a, article a, h3 a, h2 a")

        page_posts = []
        for a in anchors:
            href = a.get("href")
            title = (a.get_text() or "").strip()

            if not href or not title:
                continue

            if href.startswith("/"):
                href = BASE + href

            if href in seen_posts:
                continue

            if href.startswith(BASE):
                seen_posts.add(href)
                page_posts.append((title, href))

        for title, post_url in page_posts:
            try:
                r2 = requests.get(post_url, headers=HEADERS, timeout=10)
                r2.raise_for_status()
            except:
                continue

            soup2 = BeautifulSoup(r2.text, "html.parser")
            udemy_link = None

            for a2 in soup2.find_all("a", href=True):
                href2 = a2["href"].strip().lower()
                if "udemy.com/course" in href2:
                    udemy_link = a2["href"]
                    break

            if udemy_link:
                results.append((title, udemy_link))

            time.sleep(per_article_delay)

    return results


async def get_free_from_discudemy_async(slug=None, pages=1):
    return await asyncio.to_thread(_scrape_category_sync, slug, pages)


# -----------------------------
# Auto-check task (5 phút)
# -----------------------------
@tasks.loop(minutes=5)
async def check_new_courses():
    if CHANNEL_ID == 0:
        print("CHANNEL_ID not set")
        return

    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print("Channel not found")
        return

    print("[TASK] Checking new free courses...")

    try:
        courses = await get_free_from_discudemy_async(CATEGORY_SLUG, PAGES_TO_SCRAPE)
    except Exception as e:
        await channel.send(f"Lỗi khi lấy khóa DiscUdemy: {e}")
        return

    if not courses:
        print("[TASK] No courses found")
        return

    history = load_history()
    new_courses = []

    for title, link in courses:
        if link not in history:
            new_courses.append((title, link))
            history.append(link)

    if new_courses:
        msg = "**🎁 KHÓA UDEMY FREE MỚI VỪA XUẤT HIỆN:**\n\n"
        for title, link in new_courses[:20]:
            msg += f"• [{title}]({link})\n"

        await channel.send(msg)
        save_history(history)
    else:
        print("[TASK] No new courses")


# -----------------------------
# Manual command
# -----------------------------
@bot.command(name="free")
async def free(ctx):
    await ctx.trigger_typing()

    try:
        courses = await get_free_from_discudemy_async(CATEGORY_SLUG, PAGES_TO_SCRAPE)
    except Exception as e:
        return await ctx.send(f"Lỗi: {e}")

    if not courses:
        return await ctx.send("Không tìm thấy khóa nào.")

    msg = "**🔥 Các khóa Udemy FREE:**\n\n"
    for title, link in courses[:20]:
        msg += f"• [{title}]({link})\n"

    await ctx.send(msg)


# -----------------------------
# On Ready
# -----------------------------
@bot.event
async def on_ready():
    print(f"Bot is ready as {bot.user}")
    if not check_new_courses.is_running():
        check_new_courses.start()


# -----------------------------
# Run bot
# -----------------------------
if __name__ == "__main__":
    if not TOKEN:
        print("Please set DISCORD_TOKEN in .env")
    else:
        bot.run(TOKEN)
