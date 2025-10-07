
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import random
from typing import Optional

class BrowserTools:
    """Real web scraping and browsing tools for university research"""

    @staticmethod
    def scrape_and_summarize_website(url: str) -> str:
        """
        Scrape a website and return a summarized version of its content
        Focus on university, educational, and study abroad information
        """
        try:
            # Add headers to look like a real browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }

            # Add random delay to be respectful
            time.sleep(random.uniform(1, 3))

            # Make the request
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            # Parse HTML content
            soup = BeautifulSoup(response.content, 'html.parser')

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.extract()

            # Get page title
            title = soup.find('title')
            title_text = title.get_text().strip() if title else "No title found"

            # Extract main content areas
            content_selectors = [
                'main', 'article', '.content', '#content', 
                '.main-content', '#main-content', '.entry-content',
                '.post-content', 'section', '.container'
            ]

            main_content = None
            for selector in content_selectors:
                main_content = soup.select_one(selector)
                if main_content:
                    break

            if not main_content:
                main_content = soup.find('body')

            if not main_content:
                return f"Could not extract content from {url}"

            # Extract text content
            text_content = main_content.get_text()

            # Clean up the text
            lines = (line.strip() for line in text_content.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)

            # Limit length and create summary
            if len(text) > 2000:
                text = text[:2000] + "..."

            # Look for key university/education related information
            key_info = BrowserTools._extract_education_info(soup, text)

            summary = f"""
🌐 Website: {url}
📄 Title: {title_text}

📝 Summary:
{key_info}

📋 Full Content Preview:
{text[:500]}{"..." if len(text) > 500 else ""}
            """.strip()

            return summary

        except requests.exceptions.RequestException as e:
            return f"❌ Error accessing {url}: {str(e)}"
        except Exception as e:
            return f"❌ Error processing {url}: {str(e)}"

    @staticmethod
    def _extract_education_info(soup: BeautifulSoup, text: str) -> str:
        """Extract education-specific information from the webpage"""

        education_keywords = {
            'tuition': 'Tuition and Fees Information',
            'admission': 'Admission Requirements',
            'scholarship': 'Scholarship Opportunities',
            'international student': 'International Student Services',
            'campus': 'Campus Information',
            'program': 'Academic Programs',
            'degree': 'Degree Options',
            'application': 'Application Process',
            'deadline': 'Important Deadlines',
            'ranking': 'University Rankings',
            'accommodation': 'Housing and Accommodation',
            'visa': 'Visa Requirements'
        }

        found_info = []
        text_lower = text.lower()

        for keyword, category in education_keywords.items():
            if keyword in text_lower:
                # Find sentences containing the keyword
                sentences = text.split('.')
                relevant_sentences = [s.strip() for s in sentences if keyword in s.lower()]
                if relevant_sentences:
                    found_info.append(f"• {category}: {relevant_sentences[0][:100]}...")

        if found_info:
            return "\n".join(found_info[:5])  # Limit to top 5 findings
        else:
            return "General university/education website content found."

    @staticmethod
    def search_university_rankings(query: str) -> str:
        """
        Search for university ranking information
        This could be expanded to search specific ranking sites
        """
        ranking_sites = [
            "https://www.topuniversities.com/",
            "https://www.timeshighereducation.com/",
            "https://www.usnews.com/best-colleges"
        ]

        results = []
        for site in ranking_sites[:1]:  # Just try the first one for now
            try:
                result = BrowserTools.scrape_and_summarize_website(site)
                results.append(f"From {site}:\n{result}")
                break  # Just get one result to avoid too many requests
            except:
                continue

        if results:
            return "\n\n".join(results)
        else:
            return f"Could not retrieve ranking information for: {query}"
