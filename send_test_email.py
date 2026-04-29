
import smtplib
from email.message import EmailMessage
from datetime import datetime
import feedparser
import requests
from google import genai

import os
gmail_address = os.getenv("GMAIL_ADDRESS")
gmail_app_password = os.getenv("GMAIL_APP_PASSWORD")
gemini_api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=gemini_api_key)

feeds = {
    "AI / LLMs": [
        "https://feeds.feedburner.com/venturebeat/SZYF",
        "https://www.artificialintelligence-news.com/feed/",
    ],
    "Tech + Media Business": [
        "https://techcrunch.com/feed/",
        "https://www.theverge.com/rss/index.xml",
    ],
    "Climate / Energy": [
        "https://www.canarymedia.com/rss",
    ],
    "Marketing / CMO": [
        "https://www.marketingdive.com/feeds/news/",
    ],
}

def fetch_articles():
    articles = []

    for category, urls in feeds.items():
        category_articles = []

        for url in urls:
            response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            feed = feedparser.parse(response.text)

            for entry in feed.entries:
                category_articles.append({
                    "category": category,
                    "title": entry.get("title", "No title"),
                    "link": entry.get("link", ""),
                })

                if len(category_articles) >= 3:
                    break

            if len(category_articles) >= 3:
                break

        articles.extend(category_articles)

    return articles

def format_articles_for_prompt(articles):
    text = ""

    for article in articles:
        text += f"- Category: {article['category']}\n"
        text += f"  Headline: {article['title']}\n"
        text += f"  Link: {article['link']}\n\n"

    return text

def generate_brief_with_gemini(articles, today):
    article_text = format_articles_for_prompt(articles)

    prompt = f"""
You are writing a premium daily executive news brief in the style of TLDR + Axios.

Audience:
A senior marketing / strategy / GM leader interested in AI, media, commerce, marketing leadership, climate tech, and energy policy.

Date:
{today}

Source articles:
{article_text}

Write the full brief.

Requirements:
- Short, punchy, skimmable.
- Prioritize strategic implications over summaries.
- Do not invent facts beyond the provided headlines/links.
- Keep each "Why it matters" to one sentence.
- Use only the provided articles and links.
- Include exactly 3 articles per category if available.
- Pick the Top 5 based on likely importance to the audience.
- Keep formatting clean for plain-text email.

Format exactly:

📬 DAILY INTELLIGENCE BRIEF — {today}

========================================
🧠 TOP 5 THINGS TO KNOW
========================================

• [Headline]
  Why it matters: [Short strategic implication.]

• [Headline]
  Why it matters: [Short strategic implication.]

----------------------------------------
AI / LLMS
----------------------------------------

• [Headline]
  Why it matters: [Short strategic implication.]
  🔗 [Link]

----------------------------------------
TECH + MEDIA BUSINESS
----------------------------------------

• [Headline]
  Why it matters: [Short strategic implication.]
  🔗 [Link]

----------------------------------------
CLIMATE / ENERGY
----------------------------------------

• [Headline]
  Why it matters: [Short strategic implication.]
  🔗 [Link]

----------------------------------------
MARKETING / CMO
----------------------------------------

• [Headline]
  Why it matters: [Short strategic implication.]
  🔗 [Link]

========================================
💬 CONVERSATION STARTERS
========================================

• [Smart question or observation]
• [Smart question or observation]
• [Smart question or observation]
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-lite",
            contents=prompt
        )
        return response.text.strip()

    except Exception as e:
        print("Gemini failed. Sending fallback brief.")
        print(e)
        return None

def smart_fallback_why(article):
    title = article["title"].lower()
    category = article["category"]

    if "openai" in title or "agent" in title or "llm" in title or "rag" in title:
        return "Why it matters: AI is shifting from experimentation to operational infrastructure, where reliability and control matter more."

    if "meta" in title or "amazon" in title or "google" in title or "apple" in title:
        return "Why it matters: Big Tech moves often foreshadow where consumer platforms, media, and commerce are headed."

    if "china" in title or "europe" in title or "sovereign" in title:
        return "Why it matters: Geopolitics is increasingly shaping the technology stack companies can build and buy."

    if "solar" in title or "renewable" in title or "energy" in title or "farm bill" in title:
        return "Why it matters: Policy and infrastructure are becoming the real bottlenecks for the energy transition."

    if "brand" in title or "marketing" in title or "ctv" in title or "customer" in title:
        return "Why it matters: Marketers are under pressure to prove performance while adapting to fragmented channels and AI."

    return f"Why it matters: This could point to a broader shift in {category.lower()}."

def generate_fallback_brief(articles, today):
    digest = f"📬 DAILY INTELLIGENCE BRIEF — {today}\n\n"

    digest += "=" * 40 + "\n"
    digest += "🧠 TOP 5 THINGS TO KNOW\n"
    digest += "=" * 40 + "\n\n"

    priority_keywords = [
        "openai", "agent", "llm", "rag", "china", "europe",
        "meta", "amazon", "google", "solar", "energy", "policy",
        "marketing", "brand", "ctv"
    ]

    ranked_articles = sorted(
        articles,
        key=lambda a: any(k in a["title"].lower() for k in priority_keywords),
        reverse=True
    )

    for article in ranked_articles[:5]:
        digest += f"• {article['title']}\n"
        digest += f"  {smart_fallback_why(article)}\n\n"

    for category in feeds.keys():
        digest += "\n" + "-" * 40 + "\n"
        digest += f"{category.upper()}\n"
        digest += "-" * 40 + "\n\n"

        category_articles = [a for a in articles if a["category"] == category]

        for article in category_articles:
            digest += f"• {article['title']}\n"
            digest += f"  {smart_fallback_why(article)}\n"
            digest += f"  🔗 {article['link']}\n\n"

    digest += "\n" + "=" * 40 + "\n"
    digest += "💬 CONVERSATION STARTERS\n"
    digest += "=" * 40 + "\n\n"
    digest += "• Which AI shift is moving from hype into real operating risk or advantage?\n"
    digest += "• Which platform move could reshape media, commerce, or marketing strategy?\n"
    digest += "• Where is policy creating the biggest opening or bottleneck in climate and energy?\n"

    return digest

    digest += "=" * 40 + "\n"
    digest += "🧠 TOP 5 THINGS TO KNOW\n"
    digest += "=" * 40 + "\n\n"

    for article in articles[:5]:
        digest += f"• {article['title']}\n"
        digest += f"  Why it matters: This may signal a broader shift in {article['category'].lower()}.\n\n"

    for category in feeds.keys():
        digest += "\n" + "-" * 40 + "\n"
        digest += f"{category.upper()}\n"
        digest += "-" * 40 + "\n\n"

        category_articles = [a for a in articles if a["category"] == category]

        for article in category_articles:
            digest += f"• {article['title']}\n"
            digest += f"  Why it matters: This may signal a broader shift in {category.lower()}.\n"
            digest += f"  🔗 {article['link']}\n\n"

    digest += "\n" + "=" * 40 + "\n"
    digest += "💬 CONVERSATION STARTERS\n"
    digest += "=" * 40 + "\n\n"
    digest += "• Which AI shift is most likely to change how marketers or operators work this quarter?\n"
    digest += "• Which company move signals a bigger platform, media, or commerce shift?\n"
    digest += "• Where is climate or energy policy creating opportunity versus uncertainty?\n"

    return digest

today = datetime.now().strftime("%B %d, %Y")
articles = fetch_articles()

brief = generate_brief_with_gemini(articles, today)

if not brief:
    brief = generate_fallback_brief(articles, today)

msg = EmailMessage()
msg["Subject"] = f"Daily Intelligence Brief — {today}"
msg["From"] = gmail_address
msg["To"] = gmail_address
msg.set_content(brief)

with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
    smtp.starttls()
    smtp.login(gmail_address, gmail_app_password)
    smtp.send_message(msg)

print("Daily Intelligence Brief sent!")
