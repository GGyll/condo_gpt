# app.py
import os
from uuid import uuid4

import sqlparse
from flask import Flask, render_template, request, session
from flask_cors import CORS

from main import process_question

app = Flask(__name__)


app.secret_key = os.getenv("FLASK_SECRET")

CORS(app, resources={r"/*": {"origins": "*"}})


def format_sql(sql):
    return sqlparse.format(sql, reindent=True, keyword_case="upper")


MAX_CONTEXT_LENGTH = 3  # Number of previous exchanges to keep


def get_conversation_history():
    if "conversation_history" not in session:
        session["conversation_history"] = []
    return session["conversation_history"]


def add_to_conversation_history(question, answer):
    history = get_conversation_history()
    history.append({"question": question, "answer": answer})
    if len(history) > MAX_CONTEXT_LENGTH:
        history.pop(0)
    session["conversation_history"] = history


@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    formatted_query = None
    if "user_id" not in session:
        session["user_id"] = str(uuid4())
    if request.method == "POST":
        if request.form.get("sign_out", None):
            session.clear()
            return render_template("index.html", result=result, query=formatted_query)
        question = request.form["question"]
        conversation_history = get_conversation_history()
        result = process_question(question, conversation_history)
        add_to_conversation_history(question, result)

    return render_template(
        "index.html",
        gmaps_api_key=os.getenv("GPLACES_API_KEY"),
        result=result,
        query=formatted_query,
    )


if __name__ == "__main__":
    app.run(debug=True)
