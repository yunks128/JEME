#!/usr/bin/env python3
"""
Test script to fix first 10 ECCO papers to verify the approach works.
"""

import json
import requests
import time
import re
from typing import Dict, Any, Optional

def fetch_paper_metadata(doi: str) -> Optional[Dict[str, Any]]:
    """Fetch paper metadata from CrossRef API using DOI."""
    if not doi:
        return None
    
    # Clean DOI - remove any prefixes
    clean_doi = doi.replace('https://doi.org/', '').replace('http://dx.doi.org/', '')
    
    try:
        # Use CrossRef API
        url = f"https://api.crossref.org/works/{clean_doi}"
        headers = {
            'User-Agent': 'ECCO-Papers-Fixer/1.0 (mailto:admin@example.com)'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        work = data.get('message', {})
        
        # Extract metadata
        title = work.get('title', [''])[0] if work.get('title') else ''
        
        # Get journal name
        journal = ''
        if 'container-title' in work and work['container-title']:
            journal = work['container-title'][0]
        elif 'publisher' in work:
            journal = work['publisher']
            
        # Get publication year
        year = None
        if 'published-print' in work:
            date_parts = work['published-print'].get('date-parts', [[]])[0]
            if date_parts:
                year = date_parts[0]
        elif 'published-online' in work:
            date_parts = work['published-online'].get('date-parts', [[]])[0]
            if date_parts:
                year = date_parts[0]
        elif 'created' in work:
            date_parts = work['created'].get('date-parts', [[]])[0]
            if date_parts:
                year = date_parts[0]
        
        return {
            'title': title.strip(),
            'journal': journal.strip(),
            'year': year
        }
        
    except Exception as e:
        print(f"Error fetching metadata for DOI {doi}: {e}")
        return None

def test_first_papers():
    """Test the fix on first 10 papers."""
    input_file = '/home/kyun/science-model-dashboard/public/data/ecco_team_papers.json'
    
    print("Loading ECCO papers JSON file...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    papers = data.get('ECCO', [])[:10]  # Only first 10 for testing
    
    for i, paper in enumerate(papers):
        print(f"\n--- Paper {i+1} ---")
        doi = paper.get('doi', '')
        print(f"DOI: {doi}")
        print(f"Current title: {paper.get('title', '')[:100]}...")
        print(f"Current journal: {paper.get('journal', '')}")
        print(f"Current year: {paper.get('year')}")
        
        # Fetch metadata
        metadata = fetch_paper_metadata(doi)
        if metadata:
            print(f"Fetched title: {metadata['title']}")
            print(f"Fetched journal: {metadata['journal']}")
            print(f"Fetched year: {metadata['year']}")
        else:
            print("Failed to fetch metadata")
        
        time.sleep(1)  # Be nice to API

if __name__ == '__main__':
    test_first_papers()