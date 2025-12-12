"""Data fetching module for Google Scholar profiles."""
import argparse
import json
import logging
from typing import Optional, List, Dict, Any
import requests
from scholarly import scholarly, ProxyGenerator
from fake_useragent import UserAgent

# Logger config
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_proxy() -> bool:
    """Sets up a free proxy generator and custom session.
    
    Returns:
        bool: True if proxy was set successfully, False otherwise.
    """
    logger.info("Setting up proxy and session...")
    
    # Note: Newer versions of scholarly may not support set_session
    # Try to set custom headers via the navigator if available
    try:
        # Try to set custom user agent via navigator
        if hasattr(scholarly, '_navigator') and hasattr(scholarly._navigator, 'set_user_agent'):
            try:
                ua = UserAgent()
                user_agent = ua.random
            except Exception:
                user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            scholarly._navigator.set_user_agent(user_agent)
    except Exception as e:
        logger.debug(f"Could not set custom user agent: {e}")

    try:
        pg = ProxyGenerator()
        # Try free proxies (may fail due to API changes or availability)
        try:
            if pg.FreeProxies():
                logger.info("Proxy set successfully.")
                scholarly.use_proxy(pg)
                return True
            else:
                logger.warning("Failed to set proxy. Proceeding without proxy.")
                return False
        except TypeError as e:
            # Handle API changes in FreeProxies
            logger.warning(f"FreeProxies API may have changed: {e}. Proceeding without proxy.")
            return False
    except Exception as e:
        logger.warning(f"Proxy setup failed with error: {e}. Proceeding without proxy.")
        return False

def fetch_by_id(scholar_id: str, limit: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """Fetches author data by Scholar ID.
    
    Args:
        scholar_id: Google Scholar ID of the author.
        limit: Maximum number of publications to fetch full details for.
    
    Returns:
        Dictionary containing author data, or None if fetch failed.
    """
    logger.info(f"Fetching author with ID: {scholar_id}")
    try:
        author = scholarly.search_author_id(scholar_id)
        logger.info(f"Found author: {author.get('name', 'Unknown')} (ID: {author.get('scholar_id', 'N/A')})")
        
        # Fill data
        author = scholarly.fill(author, sections=['basics', 'indices', 'counts', 'publications'])
        
        # Process publications
        pubs_to_process = author.get('publications', [])
        if limit and limit > 0:
            pubs_to_process = pubs_to_process[:limit]
            logger.info(f"Limiting detailed fetch to first {limit} publications.")
            
        full_pubs = []
        total_pubs = len(pubs_to_process)
        for i, pub in enumerate(pubs_to_process, 1):
            title = pub.get('bib', {}).get('title', 'Unknown')
            logger.info(f"Fetching details for publication {i}/{total_pubs}: {title}")
            try:
                full_pub = scholarly.fill(pub)
                full_pubs.append(full_pub)
            except Exception as e:
                logger.warning(f"Failed to fill publication {i}: {e}")
                full_pubs.append(pub)

        author['publications'] = full_pubs
        return author
    except Exception as e:
        logger.error(f"Error fetching by ID: {e}")
        return None

def search_candidates(author_name: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """Matches authors by name and returns a list of candidates.
    
    Args:
        author_name: Name of the author to search for.
        max_results: Maximum number of candidates to return.
    
    Returns:
        List of candidate author dictionaries.
    """
    logger.info(f"Searching for candidates matching: {author_name}")
    try:
        search_query = scholarly.search_author(author_name)
        candidates = []
        for _ in range(max_results):
            try:
                author = next(search_query)
                candidates.append(author)
            except StopIteration:
                break
        return candidates
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return []

def main():
    parser = argparse.ArgumentParser(description="Fetch Google Scholar data.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--author", type=str, help="Name of the author to search.")
    group.add_argument("--id", type=str, help="Google Scholar ID of the author.")
    
    parser.add_argument("--limit", type=int, default=10, help="Limit number of publications to fetch details for (default 10).")
    parser.add_argument("--output", type=str, default="author_data.json", help="Output JSON file.")
    
    args = parser.parse_args()
    
    setup_proxy()
    
    if args.id:
        data = fetch_by_id(args.id, args.limit)
    else:
        # Search mode
        candidates = search_candidates(args.author)
        if not candidates:
            logger.info("No candidates found.")
            return
            
        if len(candidates) == 1:
            logger.info("Single match found. Fetching data...")
            data = fetch_by_id(candidates[0]['scholar_id'], args.limit)
        else:
            print(f"\nMultiple candidates found for '{args.author}':")
            for i, c in enumerate(candidates, 1):
                name = c.get('name', 'Unknown')
                scholar_id = c.get('scholar_id', 'N/A')
                affiliation = c.get('affiliation', 'No affiliation')
                print(f"{i}. {name} (ID: {scholar_id}) - {affiliation}")
            
            print("\nPlease re-run with --id <ID> to fetch specific data.")
            return

    if data:
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, default=str)
            logger.info(f"Data saved to {args.output}")
        except IOError as e:
            logger.error(f"Failed to save data to {args.output}: {e}")
    else:
        logger.error("No data fetched.")

if __name__ == "__main__":
    main()
