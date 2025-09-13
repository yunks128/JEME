#!/usr/bin/env python3
"""
Script to fix HTML entity encoding in ECCO team papers JSON file.
"""

import json
import html
import re

def fix_html_entities_in_text(text):
    """Fix HTML entities in text strings."""
    if not isinstance(text, str):
        return text
    
    # Decode HTML entities
    text = html.unescape(text)
    
    # Fix common encoding issues
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')
    text = text.replace('&#39;', "'")
    
    return text

def fix_paper_data(paper):
    """Fix HTML entities in a paper object."""
    if isinstance(paper, dict):
        fixed_paper = {}
        for key, value in paper.items():
            if isinstance(value, str):
                fixed_paper[key] = fix_html_entities_in_text(value)
            else:
                fixed_paper[key] = value
        return fixed_paper
    return paper

def fix_ecco_html_entities():
    """Main function to fix HTML entities in ECCO papers."""
    input_file = '/home/kyun/science-model-dashboard/public/data/ecco_team_papers.json'
    
    print("Loading ECCO papers JSON file...")
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading file: {e}")
        return
    
    papers = data.get('ECCO', [])
    print(f"Found {len(papers)} papers to fix")
    
    fixed_count = 0
    for i, paper in enumerate(papers):
        original_authors = paper.get('authors', '')
        original_title = paper.get('title', '')
        original_journal = paper.get('journal', '')
        
        # Fix the paper
        papers[i] = fix_paper_data(paper)
        
        # Check if anything was changed
        if (original_authors != papers[i].get('authors', '') or 
            original_title != papers[i].get('title', '') or 
            original_journal != papers[i].get('journal', '')):
            fixed_count += 1
            if fixed_count <= 10:  # Show first 10 fixes
                print(f"Fixed paper {i+1}: {papers[i].get('title', '')[:60]}...")
    
    print(f"Fixed HTML entities in {fixed_count} papers")
    
    # Save the fixed data back to the same file
    print("Saving fixed data...")
    with open(input_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print("Done! HTML entities have been fixed.")

if __name__ == '__main__':
    fix_ecco_html_entities()