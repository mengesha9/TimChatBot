import requests
from bs4 import BeautifulSoup
import logging
from typing import List, Dict, Set
import re
import json
from datetime import datetime
import time
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

    def get_chunked_documentation(self, query: str, chunk_size: int = 1000) -> List[Dict[str, str]]:
        """
        Search documentation and return chunked results.
        
        Args:
            query: The search query
            chunk_size: Size of each chunk
            
        Returns:
            List of dictionaries containing chunked documentation
        """
        results = self.search_documentation(query)
        chunks = []
        
        for result in results:
            # Create a Document object for the text splitter
            doc = Document(
                page_content=result["content"],
                metadata={
                    "title": result["title"],
                    "url": result["url"],
                    "snippet": result["snippet"]
                }
            )
            
            # Split the document into chunks
            doc_chunks = self.text_splitter.split_documents([doc])
            
            # Convert chunks to the desired format
            for chunk in doc_chunks:
                chunks.append({
                    "title": chunk.metadata["title"],
                    "content": chunk.page_content,
                    "url": chunk.metadata["url"],
                    "snippet": chunk.metadata["snippet"]
                })
        
        return chunks

class NetSuiteScraper:
    def __init__(self):
        self.base_url = "https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.visited_urls = set()
        self.delay = 1  # Delay between requests in seconds

    def get_page_content(self, url: str) -> str:
        try:
            if url in self.visited_urls:
                return ""
                
            print(f"Fetching page: {url}")
            time.sleep(self.delay)  # Be nice to the server
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            self.visited_urls.add(url)
            return response.text
        except Exception as e:
            print(f"Error fetching page {url}: {str(e)}")
            return ""

    def extract_links(self, soup: BeautifulSoup, base_url: str) -> Set[str]:
        """Extract all documentation links from the page."""
        links = set()
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.endswith('.html'):
                full_url = urljoin(base_url, href)
                if full_url.startswith(self.base_url) and full_url not in self.visited_urls:
                    links.add(full_url)
        return links

    def parse_content(self, html_content: str, url: str) -> Dict[str, str]:
        soup = BeautifulSoup(html_content, 'html.parser')
        
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
                return {"title": title_text, "content": "", "url": url}

        # Remove unwanted elements
        for element in content_div.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            element.decompose()

        # Get text content
        content = content_div.get_text(separator='\n', strip=True)
        
        # Clean up content
        content = re.sub(r'\n\s*\n', '\n\n', content)
        content = re.sub(r'\s+', ' ', content)

        return {
            "title": title_text,
            "content": content,
            "url": url
        }

    def scrape_page(self, url: str) -> List[Dict[str, str]]:
        """Scrape a single page and its linked pages recursively."""
        pages = []
        html_content = self.get_page_content(url)
        
        if not html_content:
            return pages

        # Parse current page
        page_data = self.parse_content(html_content, url)
        if page_data["content"]:
            pages.append(page_data)
            print(f"Successfully processed: {page_data['title']}")

        # Extract and follow links
        soup = BeautifulSoup(html_content, 'html.parser')
        links = self.extract_links(soup, url)
        
        for link in links:
            if link not in self.visited_urls:
                linked_pages = self.scrape_page(link)
                pages.extend(linked_pages)

        return pages

    def get_documentation_pages(self, save_to_file: bool = True, output_format: str = 'txt') -> List[Dict[str, str]]:
        print("\nStarting to scrape NetSuite documentation...")
        print(f"Save to file: {save_to_file}")
        print(f"Output format: {output_format}")
        
        # Start with the main documentation page
        main_url = f"{self.base_url}/set_N20140200.html"
        pages = self.scrape_page(main_url)
        
        print(f"\nScraping complete. Processed {len(self.visited_urls)} unique pages.")
        print(f"Total content pages: {len(pages)}")
        
        if save_to_file and pages:
            self.save_documentation_to_file(pages, output_format)
            
        return pages

    def save_documentation_to_file(self, pages: List[Dict[str, str]], output_format: str = 'txt') -> str:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if output_format == 'json':
            filename = f'netsuite_docs_{timestamp}.json'
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(pages, f, indent=2, ensure_ascii=False)
        else:  # txt format
            filename = f'netsuite_docs_{timestamp}.txt'
            with open(filename, 'w', encoding='utf-8') as f:
                for page in pages:
                    f.write(f"Title: {page['title']}\n")
                    f.write(f"URL: {page['url']}\n")
                    f.write("Content:\n")
                    f.write(page['content'])
                    f.write("\n\n" + "="*80 + "\n\n")
        
        print(f"\nDocumentation saved to: {filename}")
        print(f"Total pages saved: {len(pages)}")
        print(f"Total content size: {sum(len(page['content']) for page in pages)} characters")
        return filename

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