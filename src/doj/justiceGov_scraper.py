import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

url = "https://www.justice.gov/usao-nm/pr"

response = requests.get(url, timeout=30)

print("HTTP status:", response.status_code)

response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

article_links = []

soup = BeautifulSoup(response.text, "html.parser")

article_links = []

for link in soup.find_all("a", href=True):
    full_url = urljoin(url, link["href"])

    if "/usao-nm/pr/" in full_url:
        if full_url not in article_links:
            article_links.append(full_url)
            print(link.get_text(strip=True))
            print(full_url)
            print()

print("Article links found:", len(article_links))

print("\nFinal URL:", response.url)

title = soup.find("title")
print("Page title:", title.get_text(strip=True) if title else "No title")

all_links = soup.find_all("a", href=True)
print("Total hyperlinks:", len(all_links))

print("\nFirst 10 hyperlink addresses:")
for link in all_links[:10]:
    print(link["href"])

print("\nFirst 1,000 characters of the response:")
print(response.text[:1000])