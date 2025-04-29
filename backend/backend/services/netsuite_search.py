import requests
from bs4 import BeautifulSoup
import logging
from typing import List, Dict
import re
from urllib.parse import urljoin
from langchain_community.utilities import SerpAPIWrapper
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document

class NetSuiteSearch:
    def __init__(self, serpapi_api_key: str):
        self.search = SerpAPIWrapper(serpapi_api_key=serpapi_api_key)
        self.base_url = "https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )

    def search_documentation(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        """
        Search NetSuite documentation using SerpAPI and process the results.
        
        Args:
            query: The search query
            num_results: Number of results to return
            
        Returns:
            List of dictionaries containing processed documentation
        """
        # Add site: filter to restrict search to NetSuite docs
        search_query = f"site:docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/ {query}"
        
        try:
            # Get search results
            results = self.search.results(search_query, num_results)
            
            processed_results = []
            for result in results:
                if 'link' in result and result['link'].startswith(self.base_url):
                    # Fetch and process the page content
                    content = self.get_page_content(result['link'])
                    if content:
                        processed_results.append({
                            "title": result.get('title', ''),
                            "url": result['link'],
                            "content": content,
                            "snippet": result.get('snippet', '')
                        })
            
            return processed_results
            
        except Exception as e:
            print(f"Error searching documentation: {str(e)}")
            return []

    def get_page_content(self, url: str) -> str:
        """Fetch and process a single documentation page."""
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract title
            title = soup.find('h1')
            title_text = title.text.strip() if title else ""
            
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
                    break

            if not content_div:
                content_div = soup.find('body')
                if not content_div:
                    return ""

            # Remove unwanted elements
            for element in content_div.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                element.decompose()

            # Get text content
            content = content_div.get_text(separator='\n', strip=True)
            
            # Clean up content
            content = re.sub(r'\n\s*\n', '\n\n', content)
            content = re.sub(r'\s+', ' ', content)
            
            return content
            
        except Exception as e:
            print(f"Error fetching page {url}: {str(e)}")
            return "" 