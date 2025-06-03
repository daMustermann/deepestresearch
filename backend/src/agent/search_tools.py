import requests
from typing import List, Optional
from pydantic import BaseModel
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SearchResultItem(BaseModel):
    """Represents a single search result item."""
    url: str
    title: str
    snippet: Optional[str] = None

class SearchResults(BaseModel):
    """Represents a list of search results."""
    results: List[SearchResultItem]

def brave_search(query: str, api_key: str) -> Optional[SearchResults]:
    """
    Performs a search using the Brave Search API.

    Args:
        query: The search query string.
        api_key: The Brave Search API key.

    Returns:
        A SearchResults object containing the search results, or None if an error occurs.
    """
    logger.info(f"Performing Brave search for query: {query}")
    headers = {
        "Accept": "application/json",
        "X-Subscription-Token": api_key,
    }
    params = {"q": query}
    try:
        response = requests.get(
            "https://api.search.brave.com/res/v1/web/search",
            params=params,
            headers=headers,
            timeout=10, # Added timeout
        )
        response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
        data = response.json()

        results = []
        if "web" in data and "results" in data["web"]:
            for item in data["web"]["results"]:
                results.append(
                    SearchResultItem(
                        url=item.get("url", ""),
                        title=item.get("title", ""),
                        snippet=item.get("snippet", ""),
                    )
                )
        else:
            logger.warning("Brave search response did not contain 'web.results'.")
            if "warnings" in data:
                logger.warning(f"Brave API warnings: {data['warnings']}")
            if "errors" in data:
                logger.error(f"Brave API errors: {data['errors']}")


        return SearchResults(results=results)

    except requests.exceptions.RequestException as e:
        logger.error(f"Brave search request failed: {e}")
        return None
    except ValueError as e: # Handles JSON decoding errors
        logger.error(f"Error decoding Brave search JSON response: {e}")
        return None


def searxng_search(query: str, base_url: str) -> Optional[SearchResults]:
    """
    Performs a search using a self-hosted SearxNG instance.

    Args:
        query: The search query string.
        base_url: The base URL of the SearxNG instance (e.g., "http://localhost:8888").

    Returns:
        A SearchResults object containing the search results, or None if an error occurs.
    """
    logger.info(f"Performing SearxNG search for query: {query} on instance: {base_url}")
    # Ensure base_url does not end with a slash to avoid double slashes
    if base_url.endswith("/"):
        base_url = base_url[:-1]

    search_url = f"{base_url}/search"
    params = {"q": query, "format": "json"}

    try:
        response = requests.get(search_url, params=params, timeout=10) # Added timeout
        response.raise_for_status()
        data = response.json()

        results = []
        if "results" in data:
            for item in data["results"]:
                results.append(
                    SearchResultItem(
                        url=item.get("url", ""),
                        title=item.get("title", ""),
                        snippet=item.get("content", ""), # SearxNG often uses 'content' for snippet
                    )
                )
        else:
            logger.warning("SearxNG search response did not contain 'results'.")

        return SearchResults(results=results)

    except requests.exceptions.RequestException as e:
        logger.error(f"SearxNG search request failed: {e}")
        return None
    except ValueError as e: # Handles JSON decoding errors
        logger.error(f"Error decoding SearxNG search JSON response: {e}")
        return None

if __name__ == '__main__':
    # This is for basic testing, replace with actual API keys and base URLs
    print("Testing Brave Search (requires BRAVE_API_KEY environment variable):")
    brave_api_key_env = "YOUR_BRAVE_API_KEY" # Replace with your key or load from env
    if brave_api_key_env != "YOUR_BRAVE_API_KEY":
        brave_results = brave_search("latest AI advancements", brave_api_key_env)
        if brave_results:
            for res in brave_results.results:
                print(f"  Title: {res.title}\n  URL: {res.url}\n  Snippet: {res.snippet}\n---")
        else:
            print("Brave search returned no results or an error occurred.")
    else:
        print("Skipping Brave Search test as API key is not set.")

    print("\nTesting SearxNG Search (requires a running SearxNG instance):")
    searxng_base_url_env = "http://localhost:8888" # Replace with your SearxNG URL
    # Example of how you might check if a test URL is provided
    # import os
    # searxng_base_url_env = os.environ.get("SEARXNG_TEST_URL", "http://localhost:8888")

    # A simple check to see if the default URL is being used, you might want to skip if it is.
    if searxng_base_url_env: # Basic check
        searx_results = searxng_search("benefits of open source", searxng_base_url_env)
        if searx_results:
            for res in searx_results.results:
                print(f"  Title: {res.title}\n  URL: {res.url}\n  Snippet: {res.snippet}\n---")
        else:
            print("SearxNG search returned no results or an error occurred.")
    else:
        print("Skipping SearxNG test as base URL is not set.")
