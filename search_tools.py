# Simple, Authentic Search Tools - No Mocks, Just Real Functionality

import requests
from bs4 import BeautifulSoup
import json
import time


class SearchTools:
    """
    Simple, honest search tools that actually work
    No fake data, no elaborate mocking - just basic web searching
    """
    
    @staticmethod
    def search_internet(query: str) -> str:
        """
        Basic web search using DuckDuckGo's instant answer API
        Returns actual search results, not fake data
        """
        try:
            # Use DuckDuckGo's simple API - no key required
            url = f"https://api.duckduckgo.com/"
            params = {
                'q': query,
                'format': 'json',
                'no_html': '1',
                'skip_disambig': '1'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            results = []
            
            # Get abstract if available
            if data.get('Abstract'):
                results.append(f"Summary: {data['Abstract']}")
            
            # Get related topics
            if data.get('RelatedTopics'):
                results.append("\nRelated Information:")
                for topic in data['RelatedTopics'][:3]:  # Limit to 3
                    if isinstance(topic, dict) and topic.get('Text'):
                        results.append(f"• {topic['Text']}")
            
            # Get instant answer
            if data.get('Answer'):
                results.append(f"\nDirect Answer: {data['Answer']}")
            
            return "\n".join(results) if results else f"No detailed results found for '{query}'. Try a more specific search term."
            
        except Exception as e:
            return f"Search failed: {str(e)}. Check your internet connection."
    
    @staticmethod
    def search_university_websites(query: str) -> str:
        """
        Simple university-focused search
        Just searches for university + query terms
        """
        university_query = f"university {query} site:edu"
        return SearchTools.search_internet(university_query)
    
    @staticmethod
    def search_educational_databases(query: str) -> str:
        """
        Search educational resources
        Focuses on common educational sites
        """
        edu_sites = [
            "site:collegeboard.org",
            "site:petersons.com", 
            "site:usnews.com/best-colleges",
            "site:timeshighereducation.com"
        ]
        
        results = []
        for site in edu_sites[:2]:  # Limit to 2 sites to avoid rate limiting
            try:
                site_query = f"{query} {site}"
                result = SearchTools.search_internet(site_query)
                if result and "No detailed results found" not in result:
                    results.append(f"From {site.split(':')[1]}:\n{result}")
                time.sleep(1)  # Be respectful
            except:
                continue
        
        return "\n\n".join(results) if results else f"No educational database results found for '{query}'"