#!/usr/bin/env python3
"""
Script to extract JPL author papers from CARDAMOM_analyzed.json
"""

import json
import sys

def extract_jpl_papers():
    """Extract papers with JPL authors from CARDAMOM data."""
    input_file = '/home/kyun/science-model-dashboard/src/data/CARDAMOM_analyzed.json'
    output_file = '/home/kyun/science-model-dashboard/public/data/cardamom_team_papers.json'
    
    print("Loading CARDAMOM analyzed data...")
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            papers = json.load(f)
    except Exception as e:
        print(f"Error loading file: {e}")
        return
    
    print(f"Found {len(papers)} total papers")
    
    jpl_papers = []
    
    for i, paper in enumerate(papers):
        # Check if any author has JPL affiliation
        has_jpl_author = False
        authors = paper.get('author', [])
        
        for author in authors:
            if isinstance(author, dict):
                affiliations = author.get('affiliation', [])
                for affiliation in affiliations:
                    if isinstance(affiliation, dict):
                        name = affiliation.get('name', '')
                        if 'Jet Propulsion Laboratory' in name or 'JPL' in name:
                            has_jpl_author = True
                            break
                if has_jpl_author:
                    break
        
        if has_jpl_author:
            # Extract relevant fields for the team papers format
            title = paper.get('title', [''])
            if isinstance(title, list) and len(title) > 0:
                title = title[0]
            elif isinstance(title, str):
                title = title
            else:
                title = 'Unknown Title'
            
            # Extract author names
            author_names = []
            for author in authors:
                if isinstance(author, dict):
                    given = author.get('given', '')
                    family = author.get('family', '')
                    if given and family:
                        author_names.append(f"{given} {family}")
                    elif family:
                        author_names.append(family)
            
            authors_str = ', '.join(author_names) if author_names else 'Unknown Authors'
            
            # Extract year
            year = 'Unknown'
            published = paper.get('published-print') or paper.get('published-online')
            if published and isinstance(published, dict):
                date_parts = published.get('date-parts', [[]])
                if date_parts and len(date_parts[0]) > 0:
                    year = str(date_parts[0][0])
            
            # Extract journal
            journal = ''
            container_title = paper.get('container-title', [])
            if isinstance(container_title, list) and len(container_title) > 0:
                journal = container_title[0]
            elif isinstance(container_title, str):
                journal = container_title
            
            if not journal:
                short_container = paper.get('short-container-title', [])
                if isinstance(short_container, list) and len(short_container) > 0:
                    journal = short_container[0]
            
            # Extract DOI
            doi = paper.get('DOI', '')
            
            # Extract citation count
            citations = paper.get('is-referenced-by-count', 0)
            
            jpl_paper = {
                'title': title,
                'authors': authors_str,
                'year': year,
                'journal': journal,
                'doi': doi,
                'citations': citations,
                'url': f"https://doi.org/{doi}" if doi else ''
            }
            
            jpl_papers.append(jpl_paper)
            
        if (i + 1) % 100 == 0:
            print(f"Processed {i + 1} papers, found {len(jpl_papers)} JPL papers so far...")
    
    print(f"Found {len(jpl_papers)} papers with JPL authors")
    
    # Sort by year (descending) and then by citations (descending)
    jpl_papers.sort(key=lambda x: (
        -int(x['year']) if x['year'].isdigit() else -9999,
        -x['citations']
    ))
    
    # Create the output structure
    output_data = {
        'CARDAMOM': jpl_papers
    }
    
    # Save to JSON file
    print(f"Saving {len(jpl_papers)} JPL papers to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print("Done! CARDAMOM JPL team papers extracted successfully.")
    
    # Show sample of extracted papers
    print("\nSample of extracted papers:")
    for i, paper in enumerate(jpl_papers[:5]):
        print(f"{i+1}. {paper['title'][:80]}...")
        print(f"   Authors: {paper['authors'][:100]}...")
        print(f"   Year: {paper['year']}, Citations: {paper['citations']}")
        print(f"   Journal: {paper['journal']}")
        print()

if __name__ == '__main__':
    extract_jpl_papers()