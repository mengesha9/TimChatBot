import requests
from bs4 import BeautifulSoup
import logging
from typing import List, Dict
import re

class NetSuiteScraper:
    def __init__(self):
        self.base_url = "https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def get_page_content(self, url: str) -> str:
        try:
            print(f"Fetching page: {url}")
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            print(f"Response status code: {response.status_code}")
            return response.text
        except Exception as e:
            print(f"Error fetching page {url}: {str(e)}")
            return ""

    def parse_content(self, html_content: str, url: str) -> Dict[str, str]:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract title
        title = soup.find('h1')
        title_text = title.text.strip() if title else ""
        print(f"Found title: {title_text}")

        # Try different content divs
        content_div = None
        possible_content_divs = [
            ('div', 'content'),
            ('div', 'body'),
            ('div', 'main-content'),
            ('div', 'topic-content'),
            ('div', 'section'),
            ('article', None),
            ('main', None)
        ]

        for tag, class_name in possible_content_divs:
            if class_name:
                content_div = soup.find(tag, class_=class_name)
            else:
                content_div = soup.find(tag)
            if content_div:
                print(f"Found content in {tag} with class {class_name}")
                break

        if not content_div:
            print(f"No content div found for URL: {url}")
            # Try to get any text content as fallback
            content_div = soup.find('body')
            if not content_div:
                return {"title": title_text, "content": ""}

        # Remove unwanted elements
        for element in content_div.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            element.decompose()

        # Get text content
        content = content_div.get_text(separator='\n', strip=True)
        
        # Clean up content
        content = re.sub(r'\n\s*\n', '\n\n', content)  # Remove multiple newlines
        content = re.sub(r'\s+', ' ', content)  # Remove extra whitespace

        print(f"Content length: {len(content)} characters")
        return {
            "title": title_text,
            "content": content,
            "url": url
        }

    def get_documentation_pages(self) -> List[Dict[str, str]]:
        print("\nStarting to scrape NetSuite documentation...")
        # Start with the main documentation page
        main_url = f"{self.base_url}/set_N20140200.html"
        print(f"Fetching main documentation page: {main_url}")
        main_content = self.get_page_content(main_url)
        
        if not main_content:
            print("Failed to fetch main documentation page")
            return []

        soup = BeautifulSoup(main_content, 'html.parser')
        pages = []
        links_found = 0
        processed_pages = 0

        # Find all documentation links
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.endswith('.html') and not href.startswith('http'):
                links_found += 1
                full_url = f"{self.base_url}/{href}"
                print(f"\nProcessing page {links_found}: {full_url}")
                page_content = self.get_page_content(full_url)
                if page_content:
                    parsed_content = self.parse_content(page_content, full_url)
                    if parsed_content["content"]:
                        pages.append(parsed_content)
                        processed_pages += 1
                        print(f"Successfully processed: {parsed_content['title']}")
                    else:
                        print(f"Failed to extract content from: {full_url}")

        print(f"\nScraping complete. Found {links_found} links, processed {processed_pages} pages.")
        return pages

    def get_chunked_documentation(self, chunk_size: int = 1000) -> List[Dict[str, str]]:
        print("\nStarting to chunk documentation...")
        pages = self.get_documentation_pages()
        chunks = []
        total_chunks = 0

        for page in pages:
            content = page["content"]
            words = content.split()
            
            for i in range(0, len(words), chunk_size):
                chunk = " ".join(words[i:i + chunk_size])
                chunks.append({
                    "title": page["title"],
                    "content": chunk,
                    "url": page["url"]
                })
                total_chunks += 1
                if total_chunks % 10 == 0:
                    print(f"Created {total_chunks} chunks so far...")

        print(f"\nChunking complete. Created {total_chunks} chunks from {len(pages)} pages.")
        return chunks 