import os, sys
# append the parent directory to the sys.path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
parent_parent_dir = os.path.dirname(parent_dir)
sys.path.append(parent_parent_dir)
__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
__data__ = os.path.join(__location__, "__data")
import asyncio
from pathlib import Path
import aiohttp
import json
from crawl4ai import AsyncWebCrawler, CacheMode
from crawl4ai.content_filter_strategy import BM25ContentFilter

# 1. File Download Processing Example
async def download_example():
    """Example of downloading files from Python.org"""
    # downloads_path = os.path.join(os.getcwd(), "downloads")
    downloads_path = os.path.join(Path.home(), ".crawl4ai", "downloads")
    os.makedirs(downloads_path, exist_ok=True)
    
    print(f"Downloads will be saved to: {downloads_path}")
    
    async with AsyncWebCrawler(
        accept_downloads=True,
        downloads_path=downloads_path,
        verbose=True
    ) as crawler:
        result = await crawler.arun(
            url="https://www.python.org/downloads/",
            js_code="""
            // Find and click the first Windows installer link
            const downloadLink = document.querySelector('a[href$=".exe"]');
            if (downloadLink) {
                console.log('Found download link:', downloadLink.href);
                downloadLink.click();
            } else {
                console.log('No .exe download link found');
            }
            """,
            delay_before_return_html=1,  # Wait 5 seconds to ensure download starts
            cache_mode=CacheMode.BYPASS
        )
        
        if result.downloaded_files:
            print("\nDownload successful!")
            print("Downloaded files:")
            for file_path in result.downloaded_files:
                print(f"- {file_path}")
                print(f"  File size: {os.path.getsize(file_path) / (1024*1024):.2f} MB")
        else:
            print("\nNo files were downloaded")

# 2. Content Filtering with BM25 Example
async def content_filtering_example():
    """Example of using the new BM25 content filtering"""
    async with AsyncWebCrawler(verbose=True) as crawler:
        # Create filter with custom query for OpenAI's blog
        content_filter = BM25ContentFilter(
            # user_query="Investment and fundraising",
            # user_query="Robotic",
            bm25_threshold=1.0
        )
        
        result = await crawler.arun(
            url="https://techcrunch.com/",
            content_filter=content_filter,
            cache_mode=CacheMode.BYPASS
        )
        
        print(f"Filtered content: {len(result.fit_markdown)}")
        print(f"Filtered content: {result.fit_markdown}")
        
        # Save html 
        with open(os.path.join(__data__, "techcrunch.html"), "w") as f:
            f.write(result.fit_html)
        
        with open(os.path.join(__data__, "filtered_content.md"), "w") as f:
            f.write(result.fit_markdown)

# 3. Local File and Raw HTML Processing Example
async def local_and_raw_html_example():
    """Example of processing local files and raw HTML"""
    # Create a sample HTML file
    sample_file = os.path.join(__data__, "sample.html")
    with open(sample_file, "w") as f:
        f.write("""
        <html><body>
            <h1>Test Content</h1>
            <p>This is a test paragraph.</p>
        </body></html>
        """)
    
    async with AsyncWebCrawler(verbose=True) as crawler:
        # Process local file
        local_result = await crawler.arun(
            url=f"file://{os.path.abspath(sample_file)}"
        )
        
        # Process raw HTML
        raw_html = """
        <html><body>
            <h1>Raw HTML Test</h1>
            <p>This is a test of raw HTML processing.</p>
        </body></html>
        """
        raw_result = await crawler.arun(
            url=f"raw:{raw_html}"
        )
        
        # Clean up
        os.remove(sample_file)
        
        print("Local file content:", local_result.markdown)
        print("\nRaw HTML content:", raw_result.markdown)

# 4. Browser Management Example
async def browser_management_example():
    """Example of using enhanced browser management features"""
    # Use the specified user directory path
    user_data_dir = os.path.join(Path.home(), ".crawl4ai", "browser_profile")
    os.makedirs(user_data_dir, exist_ok=True)
    
    print(f"Browser profile will be saved to: {user_data_dir}")
    
    async with AsyncWebCrawler(
        use_managed_browser=True,
        user_data_dir=user_data_dir,
        headless=False,
        verbose=True
    ) as crawler:

        result = await crawler.arun(
            url="https://crawl4ai.com",
            # session_id="persistent_session_1",
            cache_mode=CacheMode.BYPASS
        )        
        # Use GitHub as an example - it's a good test for browser management
        # because it requires proper browser handling
        result = await crawler.arun(
            url="https://github.com/trending",
            # session_id="persistent_session_1",
            cache_mode=CacheMode.BYPASS
        )
        
        print("\nBrowser session result:", result.success)
        if result.success:
            print("Page title:", result.metadata.get('title', 'No title found'))

# 5. API Usage Example
async def api_example():
    """Example of using the new API endpoints"""
    api_token = os.getenv('CRAWL4AI_API_TOKEN') or "test_api_code"
    headers = {'Authorization': f'Bearer {api_token}'}    
    async with aiohttp.ClientSession() as session:
        # Submit crawl job
        crawl_request = {
            "urls": ["https://news.ycombinator.com"],  # Hacker News as an example
            "extraction_config": {
                "type": "json_css",
                "params": {
                    "schema": {
                        "name": "Hacker News Articles",
                        "baseSelector": ".athing",
                        "fields": [
                            {
                                "name": "title",
                                "selector": ".title a",
                                "type": "text"
                            },
                            {
                                "name": "score",
                                "selector": ".score",
                                "type": "text"
                            },
                            {
                                "name": "url",
                                "selector": ".title a",
                                "type": "attribute",
                                "attribute": "href"
                            }
                        ]
                    }
                }
            },
            "crawler_params": {
                "headless": True,
                # "use_managed_browser": True
            },
            "cache_mode": "bypass",
            # "screenshot": True,
            # "magic": True
        }
        
        async with session.post(
            "http://localhost:11235/crawl",
            json=crawl_request,
            headers=headers
        ) as response:
            task_data = await response.json()
            task_id = task_data["task_id"]
            
            # Check task status
            while True:
                async with session.get(
                    f"http://localhost:11235/task/{task_id}",
                    headers=headers
                ) as status_response:
                    result = await status_response.json()
                    print(f"Task result: {result}")
                    
                    if result["status"] == "completed":
                        break
                    else:
                        await asyncio.sleep(1)

# Main execution
async def main():
    # print("Running Crawl4AI feature examples...")
    
    # print("\n1. Running Download Example:")
    await download_example()
    
    # print("\n2. Running Content Filtering Example:")
    await content_filtering_example()
    
    # print("\n3. Running Local and Raw HTML Example:")
    await local_and_raw_html_example()
    
    # print("\n4. Running Browser Management Example:")
    await browser_management_example()
    
    # print("\n5. Running API Example:")
    await api_example()

if __name__ == "__main__":
    asyncio.run(main())