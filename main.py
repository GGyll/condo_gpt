import ast
import os
import re

import markdown
from googlemaps import Client as GoogleMaps
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from markupsafe import Markup

# for generating the pdf report, we receive reportlab code and execute it arbitrarily
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from boilerplate import (
    building_marker_format_boilerplate,
    holding_period_boilerplate,
    javascript_map_boilerplate,
    marker_boilerplate,
    school_marker_format_boilerplate,
    two_bed_holding_period_boilerplate,
)
from prefix import SQL_PREFIX
from tools import setup_tools

# Update the following variables with your database credentials
POSTGRES_USER = os.getenv("PG_USER")
POSTGRES_PASSWORD = os.getenv("PG_PASSWORD")
POSTGRES_PORT = os.getenv("PG_PORT")
POSTGRES_DB = os.getenv("PG_DB")

connection_string = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@localhost:{POSTGRES_PORT}/{POSTGRES_DB}"

db = SQLDatabase.from_uri(connection_string)

llm = ChatOpenAI(model="gpt-4o-mini")

gmaps = GoogleMaps(os.getenv("GPLACES_API_KEY"))


prefix = SQL_PREFIX.format(
    table_names=db.get_usable_table_names(),
    marker_boilerplate=marker_boilerplate,
    holding_period_boilerplate=holding_period_boilerplate,
    two_bed_holding_period_boilerplate=two_bed_holding_period_boilerplate,
    javascript_map_boilerplate=javascript_map_boilerplate,
    building_marker_format_boilerplate=building_marker_format_boilerplate,
    school_marker_format_boilerplate=school_marker_format_boilerplate,
)

system_message = SystemMessage(content=prefix)


def query_as_list(db, query):
    res = db.run(query)
    res = [el for sub in ast.literal_eval(res) for el in sub if el]
    res = [re.sub(r"\b\d+\b", "", string).strip() for string in res]
    return list(set(res))


addresses = query_as_list(db, "SELECT address FROM core_condobuilding")
alt_names = query_as_list(db, "SELECT alt_name FROM core_condobuilding")


tools = setup_tools(db, llm)

agent_executor = create_react_agent(llm, tools, messages_modifier=system_message)


def print_sql_1(sql):
    print(
        """
The SQL query is:

{}
    """.format(
            sql
        )
    )


def extract_and_remove_html(text):
    # Pattern to match HTML code block
    html_pattern = r"```html\s*([\s\S]*?)\s*```"

    # First look for any python code
    python_pattern = (
        r'<pre\s+class="codehilite"><code\s+class="language-python">(.*?)</code></pre>'
    )
    md_pattern = r"```python(.*?)```"
    python_match = re.search(python_pattern, text, re.DOTALL | re.IGNORECASE)
    md_match = re.search(md_pattern, text, re.DOTALL)
    code_match = python_match or md_match
    if code_match:
        print(text)
        code = code_match.group(1)
        code = code.replace("&quot;", '"')
        code = code.replace("&amp;", "&")
        code = code.replace("&lt;", "<")
        code = code.replace("&gt;", ">")
        code = code.replace("&#39;", "'")
        return None, "PDF Generated!", code

    # Search for the pattern in the text
    match = re.search(html_pattern, text, re.IGNORECASE)

    if match:
        # Extract the HTML code
        html_code = match.group(1).strip()
        cleaned_html = process_html(html_code)

        # Remove the HTML code block from the original text
        text_without_html = re.sub(html_pattern, "", text, flags=re.IGNORECASE).strip()

        # Return both the extracted HTML and the text without HTML
        return Markup(cleaned_html), text_without_html, False
    # If no HTML is found, return None for HTML and the original text
    return None, text, False


def process_markdown(text):
    # Convert Markdown to HTML
    html = markdown.markdown(text, extensions=["extra", "codehilite"])
    # Wrap the result in Markup to prevent auto-escaping
    return Markup(html)


def process_html(text):
    # Regular expression to find and remove the script tag containing {gmaps_api_key}
    pattern = r"<script[^>]*\{gmaps_api_key\}[^>]*></script>"

    # Replace the matched script tag with an empty string
    return re.sub(pattern, "", text, flags=re.IGNORECASE)

# Function to detect malicious patterns
def detect_malicious_code(code):
    # Define a list of regex patterns for dangerous functions or modules
    malicious_patterns = [
        r'import\s+(sys|subprocess|shlex|socket|ctypes|signal|multiprocessing)',  # Importing dangerous modules
        r'os\.(system|popen|remove|rmdir|rename|chmod|chown|kill|fork)',  # Dangerous os methods
        r'subprocess\.(Popen|run|call|check_output)',  # Subprocess methods
        r'eval\(',  # Use of eval()
        r'exec\(',  # Use of exec()
        r'compile\(',  # Use of compile()
        r'shutil\.(copy|move|rmtree)',  # shutil file operations
        r'socket\.',  # Use of sockets for network access
        r'requests\.',  # Use of requests library
        r'urllib\.',  # Use of urllib library
        r'getattr\(', r'setattr\(',  # Reflection
        r'globals\(', r'locals\(',  # Accessing global or local variable scopes
        r'importlib\.',  # Dynamic importing
        r'input\(',  # Use of input() for potentially malicious prompts
        r'os\.exec',  # exec family in os module
        r'ast\.(literal_eval)',  # Use of ast.literal_eval() for dynamic evaluation
    ]

    for pattern in malicious_patterns:
        if re.search(pattern, code):
            print(f"Potentially dangerous pattern detected: {pattern}")
            return True
    return False

def process_question(prompted_question, conversation_history):
    context = "\n".join(
        [
            f"Q: {entry['question']}\nA: {entry['answer']}"
            for entry in conversation_history
        ]
    )
    consolidated_prompt = f"""
    Previous conversation:
    {context}

    New question: {prompted_question}

    Please answer the new question, taking into account the context from the previous conversation if relevant.
    """
    prompt = consolidated_prompt if conversation_history else prompted_question

    content = []
    for s in agent_executor.stream({"messages": [HumanMessage(content=prompt)]}):

        for msg in s.get("agent", {}).get("messages", []):
            for call in msg.tool_calls:
                if sql := call.get("args", {}).get("query", None):
                    print(print_sql_1(sql))

            print(msg.content)
            html, stripped_text, code = extract_and_remove_html(msg.content)
            if code:
                # # ----- Checking for Malicious Code
                
                # Check for malicious patterns before executing
                if not detect_malicious_code(code):
                    exec(code)

                # # ----- Checking for Malicious Code
            content.append(process_markdown(stripped_text))
            if html:
                content.append(html)
        print("----")

    return content
