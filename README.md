# Condo GPT

## Video
[![BUILD YOUR AI PORTFOLIO](https://img.youtube.com/vi/k7zFH1PYaRA/0.jpg)](https://www.youtube.com/watch?v=k7zFH1PYaRA)

Condo GPT is an intelligent assistant for querying and analyzing condominium data in Miami. It uses natural language processing to interpret user questions and provide insights about condo buildings, units, sales, and market trends.
Provided is a sample of the [Condo Cube]([https://duckduckgo.com](https://condo-cube.com/)) database which can be used to query data in the following markets:
- South Beach
- Miami Beach
- South of Fifth

The purpose is to allow real estate agents and investors who are not technical, to easily and quickly perform high-level analyses and comparisons of condos in Miami, and lead their investment decisions. Currently this job is performed by analysts which are paid a salary, so tools like these have the potential to save brokerages thousands of dollars per month in salary.

## Get an AI Engineer Job | Contributing
I used this as a portfolio project to get my first AI Engineer job. I have listed some issues which you can solve or submit your own PR's for improvements to the tool. Open source contributions are a very good way to get AI jobs since technologies like LangChain are so new, and many companies currently do not require work experience with them.

Please feel free to submit a Pull Request.

## Features

- Natural language interface for querying condo data
- Integration with Google Maps API for location-based queries
- Dynamic SQL generation for complex database queries
- Interactive maps and charts for data visualization
- PDF report generation capability

## Technologies Used

- Python 3.x
- Flask web framework
- PostgreSQL database
- LangChain & LangGraph agents
- OpenAI's GPT models for natural language understanding
- Google Maps API for geocoding and directions
- Chart.js for data visualization
- ReportLab for PDF generation

## Setup

1. Clone the repository
2. Prepare the environment and database
-  virtualenv gpt_env
-  Log in to psql as superuser (sudo -u postgres psql on Linux)
-  `CREATE DATABASE condo_gpt`;
   `CREATE USER readonly_user WITH PASSWORD 'password';`
   `GRANT CONNECT ON DATABASE condo_gpt TO readonly_user;`
   `GRANT USAGE ON SCHEMA public TO readonly_user;`
   `GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;`
   `ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO readonly_user;`
   `\q`
3. Edit your `gpt_env/bin/activate` file and add the following environment variables
- `GPLACES_API_KEY`: Your Google Places API key
- `OPENAI_API_KEY`: Your OpenAI API key
- `FLASK_SECRET` : Flask Secret Phrase (Can be any string)
- `PG_USER`: Your postgres User you set up above
- `PG_PASSWORD`: Password for your postgres user
- `PG_PORT`: Port for your postgres database server (default 5432)
- `PG_DB`: Name of your postgres database
4. Set up the sample data
-  Ensure you are in the same directory as sample_db.sql
-  `psql -d condo_gpt < sample_db.sql`
5. Install dependencies:
- `source gpt_env/bin/activate`
- `pip install -r requirements.txt`
6. Start the application
`python server.py`

## Running the Application

1. Start the Flask server:
`python server.py`
2. Open a web browser and navigate to `http://localhost:5000`

## Usage

- Enter natural language questions about Miami condos in the input field
- The system will interpret your question, query the database, and provide relevant answers
- For location-based queries, interactive maps may be generated
- The system can create charts and graphs for data visualization
- PDF reports can be generated for more detailed analysis
- Use the 'Clear Memory' Button to clear the conversation history

## Example Prompt Sequence
- What buildings on collins had the most sales in 2023?
- Generate a graph of this data
- Put the data in an html table
- Add a third column with the total sales volume of each building
- Add a fourth column with the median sales price for each building
- Replace the third column with the closest school to the building, and the fourth column with the driving distance to that school from the building

## Project Structure

- `server.py`: Flask application server
- `main.py`: Core logic for processing questions and generating responses
- `tools.py`: Custom tools for database querying and API interactions
- `prefix.py`: System message prefix for the AI agent
- `boilerplate.py`: Boilerplate code for map and chart generation
