import requests

url = ('https://newsapi.org/v2/everything?'
       'q=Meta&'
       'from=2025-10-20&'
       'sortBy=popularity&'
       'apiKey=')

response = requests.get(url)

print(response.json())
