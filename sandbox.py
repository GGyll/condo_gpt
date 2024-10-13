from langchain_community.tools import GooglePlacesTool

places = GooglePlacesTool()


res = places.run("primary school")
print(res)
