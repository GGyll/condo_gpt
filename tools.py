import ast
import os
import re
from operator import itemgetter

import markdown
import reportlab
from googlemaps import Client as GoogleMaps
from langchain.agents.agent_toolkits import create_retriever_tool
from langchain.tools import BaseTool
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_community.tools import GooglePlacesTool
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from pydantic import BaseModel, Field

google_places = GooglePlacesTool()


gmaps = GoogleMaps(os.getenv("GPLACES_API_KEY"))


class DirectionsInput(BaseModel):
    origin: str = Field(..., description="The starting point address or coordinates")
    destination: str = Field(
        ..., description="The destination point address or coordinates"
    )


class GeocodingTool(BaseTool):
    name = "google_maps_geocoding"
    description = "Useful for converting addresses into geographic coordinates."
    args_schema = DirectionsInput

    def _run(self, address):
        try:
            geocode_result = gmaps.geocode(address)
            if geocode_result:
                location = geocode_result[0]["geometry"]["location"]
                print("--- GEOCODING TOOL ---")
                print(address)
                print(location)
                print("--- GEOCODING TOOL END ---")
                return f"The coordinates for the address {address} are {location['lat']}, {location['lng']}."
            return "Unable to find coordinates for the specified address."
        except Exception as e:
            return f"An error occurred while fetching coordinates: {str(e)}"


class DirectionsTool(BaseTool):
    name = "google_maps_directions"
    description = (
        "Useful for finding travel distances and directions between two locations."
    )
    args_schema = DirectionsInput

    def _run(self, origin, destination):
        try:
            print("DIRECTIONS API: ", origin, destination)
            directions_result = gmaps.directions(origin, destination, mode="driving")
            if directions_result:
                distance = directions_result[0]["legs"][0]["distance"]["text"]
                duration = directions_result[0]["legs"][0]["duration"]["text"]
                return f"The travel distance from {origin} to {destination} is {distance}, and it takes approximately {duration} by car."
            return "Unable to find directions between the specified locations."
        except Exception as e:
            return f"An error occurred while fetching directions: {str(e)}"


directions_tool = DirectionsTool(
    description="Use to find travel distances and directions between two locations."
)

google_maps_geocoding = GeocodingTool(
    description="Use to convert addresses into geographic coordinates."
)


def query_as_list(db, query):
    res = db.run(query)
    res = [el for sub in ast.literal_eval(res) for el in sub if el]
    res = [re.sub(r"\b\d+\b", "", string).strip() for string in res]
    return list(set(res))


def setup_tools(db, llm):
    addresses = query_as_list(db, "SELECT address FROM core_condobuilding")
    alt_names = query_as_list(db, "SELECT alt_name FROM core_condobuilding")
    vector_db = FAISS.from_texts(alt_names + addresses, OpenAIEmbeddings())
    retriever = vector_db.as_retriever(search_kwargs={"k": 5})
    description = """Use to look up values to filter on. Input is an approximate spelling of the proper noun, output is \
    valid proper nouns. Use the noun most similar to the search."""
    retriever_tool = create_retriever_tool(
        retriever,
        name="search_proper_nouns",
        description=description,
    )
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    tools = toolkit.get_tools()
    tools.append(retriever_tool)
    tools.append(google_places)
    tools.append(directions_tool)
    tools.append(google_maps_geocoding)
    return tools
