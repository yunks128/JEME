#!/usr/bin/env python3
"""
Automated script to fix ECCO team papers JSON file.
Fetches correct metadata using DOI and cleans corrupted titles.
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

def clean_title(title: str) -> str:
    """Clean corrupted titles by removing common artifacts."""
    if not title:
        return ''
    
    # Remove common artifacts and concatenated text
    # Look for patterns like "word. Word" which often indicate sentence boundaries
    sentences = re.split(r'\. [A-Z]', title)
    if len(sentences) > 1:
        # Take the longest sentence as it's likely the real title
        title = max(sentences, key=len).strip()
    
    # Remove leading/trailing artifacts
    title = re.sub(r'^[^A-Z]*', '', title)  # Remove non-capital letters at start
    title = re.sub(r'\s+', ' ', title)       # Normalize whitespace
    title = title.strip()
    
    return title

def fix_ecco_papers():
    """Main function to fix ECCO papers JSON file."""
    input_file = '/home/kyun/science-model-dashboard/public/data/ecco_team_papers.json'
    output_file = '/home/kyun/science-model-dashboard/public/data/ecco_team_papers_fixed.json'
    
    print("Loading ECCO papers JSON file...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    papers = data.get('ECCO', [])
    total_papers = len(papers)
    
    print(f"Found {total_papers} papers to process")
    
    processed = 0
    fixed = 0
    errors = 0
    
    for i, paper in enumerate(papers):
        processed += 1
        doi = paper.get('doi', '')
        
        print(f"Processing paper {processed}/{total_papers}: {doi[:50]}...")
        
        # Skip if already has complete data
        if (paper.get('journal') and 
            paper.get('journal').strip() != '' and 
            paper.get('year') and 
            paper.get('title') and 
            len(paper.get('title', '').split()) < 20):  # Reasonable title length
            continue
        
        # Fetch metadata from DOI
        metadata = fetch_paper_metadata(doi)
        
        if metadata:
            # Update paper with fetched data
            if metadata['title'] and len(metadata['title']) > 10:  # Reasonable title
                paper['title'] = metadata['title']
                fixed += 1
            elif paper.get('title'):
                # Try to clean existing title
                cleaned_title = clean_title(paper['title'])
                if cleaned_title and len(cleaned_title) > 10:
                    paper['title'] = cleaned_title
                    fixed += 1
            
            if metadata['journal']:
                paper['journal'] = metadata['journal']
                
            if metadata['year']:
                paper['year'] = metadata['year']
        else:
            errors += 1
            # Try to clean existing title even if API failed
            if paper.get('title'):
                cleaned_title = clean_title(paper['title'])
                if cleaned_title and len(cleaned_title) > 10:
                    paper['title'] = cleaned_title
        
        # Rate limiting - be nice to CrossRef API
        if processed % 10 == 0:
            print(f"Progress: {processed}/{total_papers}, Fixed: {fixed}, Errors: {errors}")
            time.sleep(1)  # 1 second delay every 10 requests
        else:
            time.sleep(0.1)  # Small delay between requests
    
    print(f"\nCompleted! Processed: {processed}, Fixed: {fixed}, Errors: {errors}")
    
    # Save the fixed data
    print(f"Saving fixed data to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print("Done! Fixed data saved.")
    
    # Show some statistics
    complete_papers = sum(1 for p in papers if p.get('journal') and p.get('journal').strip())
    print(f"\nStatistics:")
    print(f"Total papers: {total_papers}")
    print(f"Papers with journal info: {complete_papers}")
    print(f"Completion rate: {complete_papers/total_papers*100:.1f}%")

if __name__ == '__main__':
    fix_ecco_papers()