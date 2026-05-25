from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
import datetime

app = Flask(__name__)

# MongoDB setup (local fallback if not running)
try:
    client = MongoClient(
        "mongodb+srv://qryenox_db_user:VsHnfoLMqlznhra1@cluster0.zdvtkgj.mongodb.net/?appName=Cluster0"
    )

    db = client["trusted_ai"]
    collection = db["search_history"]

    print("MongoDB connected.")

except Exception as e:

    print("MongoDB failed:", e)
    collection = None


def search_trusted_sources(query):

    query = f"{query} site:.gov.au OR site:.edu.au OR site:.org"

    url = "https://html.duckduckgo.com/html/"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:

        response = requests.post(
            url,
            data={"q": query},
            headers=headers,
            timeout=10
        )

        soup = BeautifulSoup(response.text, "html.parser")

        data = []

        results = soup.select(".result")

        for r in results[:5]:

            title_tag = r.select_one(".result__title")
            snippet_tag = r.select_one(".result__snippet")
            link_tag = r.select_one("a")

            if title_tag and link_tag:

                title = title_tag.get_text(strip=True)

                link = link_tag.get("href")

                summary = (
                    snippet_tag.get_text(strip=True)
                    if snippet_tag
                    else f"Information related to '{title}'."
                )

                data.append({
                    "title": title,
                    "link": link,
                    "summary": summary
                })

        return data

    except Exception as e:

        print("Search error:", e)

        return []


@app.route("/", methods=["GET", "POST"])
def home():

    answer = []
    question = ""

    if request.method == "POST":

        question = request.form["question"]

        results = search_trusted_sources(question)

        print(results)

        answer = results

        # Save to MongoDB
        if collection is not None:

            try:

                collection.insert_one({
                    "question": question,
                    "results": results,
                    "time": datetime.datetime.now()
                })

            except Exception as e:

                print("Mongo save error:", e)

    return render_template(
        "index.html",
        answer=answer,
        question=question
    )


if __name__ == "__main__":
    app.run(debug=True)