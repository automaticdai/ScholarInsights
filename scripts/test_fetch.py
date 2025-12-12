from scholarly import scholarly, ProxyGenerator
import json
import logging

# Set up logging to see what scholarly is doing
logging.basicConfig(level=logging.INFO)

def test_fetch_profile():
    print("Setting up proxy...")
    pg = ProxyGenerator()
    success = pg.FreeProxies()
    # Or pg.Tor_Internal(tor_cmd="tor") if using Tor
    if success:
        print("Proxy set.")
        scholarly.use_proxy(pg)
    else:
        print("Failed to set proxy.")
        return

    print("Searching for Andrew Ng...")
    try:
        search_query = scholarly.search_author('Andrew Ng')
        # Check if we can peek or list
        # authors = list(search_query) # This exhausts the generator
        # if not authors:
        #     print("No authors found in list.")
        #     return
        
        # author = authors[0]
        
        author = next(search_query)
        print(f"Found author: {author['name']}")
        
        print("Filling author details...")
        author = scholarly.fill(author, sections=['basics', 'indices'])
        
        print(f"Name: {author['name']}")
        print(f"Affiliation: {author.get('affiliation')}")
        print(f"Total Citations: {author.get('citedby')}")
        
    except StopIteration:
        print("Author not found.")
    except Exception as e:
        print(f"Error occurred: {e}")

if __name__ == "__main__":
    test_fetch_profile()
