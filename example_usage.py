"""
Example usage of the Grokipedia API
Run this after starting the API server with: python main.py
"""

import requests
import json
from typing import Optional

# API Base URL
API_BASE = "http://localhost:8000"


def print_json(data, indent=2):
    """Pretty print JSON data"""
    print(json.dumps(data, indent=indent))


def example_health_check():
    """Example: Check if API is healthy"""
    print("\n=== Health Check ===")
    response = requests.get(f"{API_BASE}/health")
    print(f"Status Code: {response.status_code}")
    print_json(response.json())


def example_get_stats():
    """Example: Get Grokipedia statistics"""
    print("\n=== Statistics ===")
    response = requests.get(f"{API_BASE}/stats")
    print_json(response.json())


def example_get_article(slug: str = "Joe_Biden"):
    """Example: Get a full article"""
    print(f"\n=== Getting Article: {slug} ===")
    response = requests.get(f"{API_BASE}/article/{slug}")
    
    if response.status_code == 200:
        article = response.json()
        print(f"Title: {article['title']}")
        print(f"URL: {article['url']}")
        print(f"Summary: {article['summary'][:200]}...")
        print(f"Sections: {len(article['sections'])}")
        print(f"References: {len(article['references'])}")
        print(f"Word Count: {article['metadata']['word_count']}")
        print(f"Fact Checked: {article['metadata']['fact_checked']}")
        
        print("\nTable of Contents:")
        for i, section in enumerate(article['table_of_contents'][:5], 1):
            print(f"  {i}. {section}")
        if len(article['table_of_contents']) > 5:
            print(f"  ... and {len(article['table_of_contents']) - 5} more sections")
    else:
        print(f"Error: {response.status_code}")
        print_json(response.json())


def example_get_summary(slug: str = "Joe_Biden"):
    """Example: Get article summary (faster)"""
    print(f"\n=== Getting Summary: {slug} ===")
    response = requests.get(f"{API_BASE}/article/{slug}/summary")
    
    if response.status_code == 200:
        summary = response.json()
        print(f"Title: {summary['title']}")
        print(f"Summary: {summary['summary'][:300]}...")
        print(f"\nSections: {', '.join(summary['table_of_contents'][:3])}...")
    else:
        print(f"Error: {response.status_code}")


def example_get_section(slug: str = "Joe_Biden", section: str = "Early_life"):
    """Example: Get a specific section"""
    print(f"\n=== Getting Section: {section} from {slug} ===")
    response = requests.get(f"{API_BASE}/article/{slug}/section/{section}")
    
    if response.status_code == 200:
        data = response.json()
        section_data = data['section']
        print(f"Article: {data['article_title']}")
        print(f"Section: {section_data['title']}")
        print(f"Level: H{section_data['level']}")
        print(f"Content: {section_data['content'][:300]}...")
    else:
        print(f"Error: {response.status_code}")
        print_json(response.json())


def example_api_info():
    """Example: Get API information"""
    print("\n=== API Information ===")
    response = requests.get(f"{API_BASE}/info")
    info = response.json()
    print(f"API: {info['name']} v{info['version']}")
    print(f"Description: {info['description']}")
    print("\nAvailable Endpoints:")
    for endpoint, description in info['endpoints'].items():
        print(f"  {endpoint}: {description}")


def example_for_ai_model(slug: str = "Joe_Biden"):
    """Example: Fetching content for an AI model"""
    print(f"\n=== Preparing Content for AI Model ===")
    
    # Get article
    response = requests.get(f"{API_BASE}/article/{slug}")
    
    if response.status_code == 200:
        article = response.json()
        
        # Format for AI context
        context = f"""
Article: {article['title']}
Source: {article['url']}
Fact-Checked: {article['metadata']['fact_checked']}

Summary:
{article['summary']}

Table of Contents:
{chr(10).join(f"- {section}" for section in article['table_of_contents'])}

Full Content:
{article['full_content'][:2000]}...

References:
{chr(10).join(f"- {ref}" for ref in article['references'][:5])}
"""
        
        print("Content formatted for AI model:")
        print("=" * 50)
        print(context)
        print("=" * 50)
        print(f"\nTotal length: {len(context)} characters")
        print("This context can now be passed to your AI model!")


def main():
    """Run all examples"""
    print("=" * 70)
    print("Grokipedia API - Example Usage")
    print("=" * 70)
    print("\nMake sure the API server is running: python main.py")
    print("API should be available at:", API_BASE)
    
    try:
        # Run examples
        example_health_check()
        example_api_info()
        example_get_stats()
        example_get_article("Joe_Biden")
        example_get_summary("Joe_Biden")
        example_get_section("Joe_Biden", "Early_life")
        example_for_ai_model("Joe_Biden")
        
        print("\n" + "=" * 70)
        print("Examples completed successfully!")
        print("=" * 70)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to the API")
        print("Make sure the server is running: python main.py")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")


if __name__ == "__main__":
    main()

