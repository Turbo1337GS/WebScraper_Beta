# Web Scraper

This is a web scraping script written in Python 3.10. It utilizes asyncio and aiohttp libraries to efficiently crawl web pages and extract clean text content. The script follows a breadth-first search approach to traverse through web pages, starting from an initial URL. It saves the extracted text content to multiple files, ensuring that each file does not exceed a specified size limit.

## Short Description

The web scraper script is designed to crawl web pages, extract text content, and save the content to text files. It uses asyncio and aiohttp to efficiently handle multiple requests concurrently. The script follows a breadth-first search approach to traverse through web pages, visiting each page only once. The extracted text content is cleaned and stored in multiple files, preventing any single file from exceeding a specified size limit.

## Instructions

To use the web scraper script, follow these steps:

1. Install the required dependencies by running the following command:
    ```
    pip install aiohttp lxml beautifulsoup4 readability
    ```

2. Set the desired configuration parameters in the script:
   - `MAX_QUEUE_SIZE`: Maximum number of URLs to be stored in the queue.
   - `DEPTH_LIMIT`: Maximum depth of crawling. Set to `None` for unlimited depth.
   - `FILE_NAME`: Name pattern for the output files.
   - `BUFFER_SIZE`: Number of text content entries to buffer before writing to a file.
   - `INITIAL_URL`: The starting URL for the web scraping process.
   - `NUM_WORKERS_MULTIPLIER`: Multiplier for the number of worker tasks.
   - `TCP_CONNECTOR_LIMIT_PER_HOST`: Maximum number of TCP connections per host.
   - `MAX_FILE_SIZE_MB`: Maximum size of each output file in megabytes.
   - `START_TOKEN` and `END_TOKEN`: Tokens to mark the beginning and end of each extracted text content.

3. Run the script using Python 3.10:
    ```
    python web_scraper.py
    ```

4. The script will start crawling the web pages, extracting text content, and saving it to multiple files. The progress and statistics will be displayed in the console.

## Documentation

### Class: WebScraper

#### Methods

- `__init__()`: Initializes the WebScraper class with necessary attributes and queues.
- `save_to_file()`: Saves the buffered text content to a file, maintaining the maximum file size limit.
- `get_file_size_in_mb(file_pattern)`: Returns the total size of files that match the given pattern in megabytes.
- `process_html(text)`: Processes the HTML text, extracts clean text content, and adds it to the buffer.
- `html_processor()`: Asynchronously processes the HTML text from the queue.
- `fetch(url, session, depth)`: Fetches the HTML content of a URL, extracts links, and adds them to the queue.
- `worker(session)`: Worker function that handles the crawling and fetching of URLs.
- `main()`: Main function that sets up the asyncio event loop and runs the web scraping process.

#### Attributes

- `visited`: Set to keep track of visited URLs.
- `queue`: Asynchronous queue to store URLs to be crawled.
- `html_processing_queue`: Asynchronous queue to store HTML content to be processed.
- `unique_texts`: Set to store unique text content.
- `buffered_texts`: Deque to buffer the extracted text content before writing to a file.
- `semaphore`: Semaphore to limit the number of concurrent requests.
- `current_file_index`: Index to keep track of the current output file.

## Extensive Text

The web scraper script provided is a powerful tool for crawling web pages and extracting clean text content. It utilizes asyncio and aiohttp libraries to efficiently handle multiple requests concurrently, making it suitable for scraping large websites. The script follows a breadth-first search approach, which ensures that all reachable pages are visited while keeping the depth of the crawl within a specified limit.

The script's architecture is designed to optimize performance and minimize resource usage. It uses asynchronous queues to handle URLs and HTML content, allowing multiple tasks to work concurrently. The script also implements a buffering mechanism to efficiently store and write the extracted text content to files, preventing any single file from becoming too large.

The configuration parameters provided in the script allow for customization based on specific scraping requirements. The maximum queue size limits the number of URLs that can be stored for crawling, preventing excessive memory usage. The depth limit parameter controls the depth of the crawl, allowing users to focus on specific sections of a website. The file name pattern and maximum file size parameters enable efficient storage and management of the extracted text content.

The WebScraper class provides a clean and modular structure for the web scraping functionality. Each method has a specific purpose, making the code easy to understand and modify. The class attributes efficiently store and manage the state of the scraping process, ensuring that URLs are visited only once and that unique text content is extracted and saved.

In summary, the web scraper script provided is a versatile tool for extracting text content from web pages. Its efficient implementation, customization options, and clean code structure make it suitable for a wide range of web scraping tasks. Whether you need to extract data for research, analysis, or any other purpose, this script can be a valuable asset in your toolkit.
