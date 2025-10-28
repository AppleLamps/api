"""Example usage of the Grokipedia SDK"""

from grokipedia_sdk import Client, ArticleNotFound, RequestError


def example_basic_usage():
    """Demonstrate basic SDK usage"""
    print("=" * 60)
    print("Example 1: Basic Usage")
    print("=" * 60)
    
    # Create a client instance
    client = Client()
    
    try:
        # Fetch a full article
        article = client.get_article("Joe_Biden")
        
        print(f"\nTitle: {article.title}")
        print(f"URL: {article.url}")
        print(f"\nSummary:")
        print(article.summary[:200] + "...")
        print(f"\nSections: {len(article.sections)}")
        print(f"References: {len(article.references)}")
        print(f"Word Count: {article.metadata.word_count}")
        
        if article.metadata.fact_checked:
            print(f"Fact-checked by: {article.metadata.fact_checked}")
        
        print(f"\nTable of Contents:")
        for i, section_title in enumerate(article.table_of_contents[:5], 1):
            print(f"  {i}. {section_title}")
        
    except ArticleNotFound:
        print("Article not found")
    except RequestError as e:
        print(f"Error: {e}")
    finally:
        client.close()


def example_context_manager():
    """Demonstrate using the client as a context manager"""
    print("\n" + "=" * 60)
    print("Example 2: Using Context Manager")
    print("=" * 60)
    
    # Using context manager (recommended)
    with Client() as client:
        try:
            # Get article summary (faster, less data)
            summary = client.get_summary("Joe_Biden")
            
            print(f"\nTitle: {summary.title}")
            print(f"\nSummary:")
            print(summary.summary[:300] + "...")
            
            print(f"\nTable of Contents (first 10):")
            for i, section_title in enumerate(summary.table_of_contents, 1):
                print(f"  {i}. {section_title}")
            
        except ArticleNotFound:
            print("Article not found")
        except RequestError as e:
            print(f"Error: {e}")


def example_get_section():
    """Demonstrate fetching a specific section"""
    print("\n" + "=" * 60)
    print("Example 3: Fetching Specific Section")
    print("=" * 60)
    
    with Client() as client:
        try:
            # Get a specific section
            section = client.get_section("Joe_Biden", "Early Life")
            
            if section:
                print(f"\nSection: {section.title}")
                print(f"Level: {section.level}")
                print(f"\nContent:")
                print(section.content[:500] + "...")
            else:
                print("Section not found")
                
        except ArticleNotFound:
            print("Article not found")
        except RequestError as e:
            print(f"Error: {e}")


def example_error_handling():
    """Demonstrate error handling"""
    print("\n" + "=" * 60)
    print("Example 4: Error Handling")
    print("=" * 60)
    
    with Client() as client:
        # Try to fetch a non-existent article
        try:
            article = client.get_article("This_Article_Does_Not_Exist_12345")
            print(f"Found: {article.title}")
        except ArticleNotFound:
            print("✓ ArticleNotFound exception caught correctly")
        except RequestError as e:
            print(f"RequestError: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")


def example_multiple_articles():
    """Demonstrate fetching multiple articles"""
    print("\n" + "=" * 60)
    print("Example 5: Fetching Multiple Articles")
    print("=" * 60)
    
    slugs = ["Joe_Biden", "Elon_Musk", "Artificial_Intelligence"]
    
    with Client() as client:
        for slug in slugs:
            try:
                summary = client.get_summary(slug)
                print(f"\n{summary.title}")
                print(f"  Summary: {summary.summary[:100]}...")
                print(f"  Sections: {len(summary.table_of_contents)}")
            except ArticleNotFound:
                print(f"\n✓ Article '{slug}' not found")
            except RequestError as e:
                print(f"\n✗ Error fetching '{slug}': {e}")


def example_custom_configuration():
    """Demonstrate custom configuration"""
    print("\n" + "=" * 60)
    print("Example 6: Custom Configuration")
    print("=" * 60)
    
    # Use custom timeout
    with Client(timeout=60.0) as client:
        try:
            summary = client.get_summary("Joe_Biden")
            print(f"✓ Successfully fetched with custom timeout")
            print(f"Title: {summary.title}")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    print("\nGrokipedia SDK Examples")
    print("=" * 60)
    
    # Run examples
    example_basic_usage()
    example_context_manager()
    example_get_section()
    example_error_handling()
    example_multiple_articles()
    example_custom_configuration()
    
    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)

