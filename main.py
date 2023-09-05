import asyncio
import aiohttp
from lxml.etree import ParserError
from collections import deque
from urllib.parse import urljoin, urlparse
import os
from bs4 import BeautifulSoup
from readability import Document
import glob

# Global Configuration Variables
MAX_QUEUE_SIZE = 5000000
DEPTH_LIMIT = None  # None for unlimited depth
FILE_NAME = "clean_scraped_data{}.txt"
BUFFER_SIZE = 10
INITIAL_URL = "https://pl.wikipedia.org/wiki/J%C4%99zyk_programowania"
NUM_WORKERS_MULTIPLIER = 4
TCP_CONNECTOR_LIMIT_PER_HOST = 40
MAX_FILE_SIZE_MB = 1000
START_TOKEN = "<|startoftext|>"
END_TOKEN = "<|endoftext|>"



# Main Web Scraper Class
class WebScraper:
    def __init__(self):
        self.visited = set()  # Set of visited URLs
        self.queue = asyncio.Queue(maxsize=MAX_QUEUE_SIZE)  # Async Queue for URLs to be scraped
        self.html_processing_queue = asyncio.Queue()  # Queue for raw HTML texts
        self.unique_texts = set()  # Set to keep unique text articles
        self.buffered_texts = deque()  # Deque to hold texts before writing to file
        self.semaphore = asyncio.Semaphore(5)  # Semaphore to limit the number of simultaneous connections
        self.current_file_index = 0  # Current file index to save data

    async def save_to_file(self):
        # Saves buffered text to file and update file index if needed
        current_file_name = FILE_NAME.format(self.current_file_index)
        with open(current_file_name, 'a', encoding='utf-8') as f:
            while self.buffered_texts:
                f.write(START_TOKEN)
                f.write(self.buffered_texts.popleft())
                f.write(END_TOKEN)
                f.write('\n')

        file_size = self.get_file_size_in_mb(FILE_NAME.format("*"))

        if file_size >= MAX_FILE_SIZE_MB:
            self.current_file_index += 1

        print(f"(Visited: {len(self.visited)} articles, "
              f"File size: {file_size:.2f} MB, "
              f"Queue size: {self.queue.qsize()}, "
              f"Unique texts: {len(self.unique_texts)})")

    @staticmethod
    def get_file_size_in_mb(file_pattern):
        # Calculates the total size of files that match the pattern
        total_size = 0
        for filename in glob.glob(file_pattern):
            total_size += os.path.getsize(filename)
        return total_size / (1024 * 1024)

    async def process_html(self, text):
        # Processes the raw HTML text to get a readable article
        if not text.strip():
            return

        try:
            document = Document(text)
            readable_article = document.summary()
        except ParserError:
            print("Error: Document is empty.")
            return

        soup = BeautifulSoup(readable_article, 'html.parser')
        cleaned_text = soup.text.strip()

        if len(cleaned_text) > 20:
            cleaned_content = ' '.join(cleaned_text.split())
            if cleaned_content not in self.unique_texts:
                self.unique_texts.add(cleaned_content)
                self.buffered_texts.append(cleaned_content)

                if len(self.buffered_texts) >= BUFFER_SIZE:
                    await self.save_to_file()

    async def html_processor(self):
        # Function that dequeues HTML texts from the queue and processes them
        while True:
            text = await self.html_processing_queue.get()
            await self.process_html(text)
            self.html_processing_queue.task_done()

    async def fetch(self, url, session, depth):
        # Fetches the HTML content from the URL and finds new URLs
        async with self.semaphore:
            if (DEPTH_LIMIT is not None and depth > DEPTH_LIMIT) or url in self.visited or url in self.queue._queue:
                return

            self.visited.add(url)
            try:
                async with session.get(url, ssl=False) as response:
                    if 'text/html' not in response.headers.get('content-type', ''):
                        return

                    text = await response.text(errors='replace')
                    await self.html_processing_queue.put(text)

                    for link in BeautifulSoup(text, 'html.parser').find_all('a'):
                        href = link.get('href')
                        if href and "javascript:" not in href:
                            if self.queue.qsize() < MAX_QUEUE_SIZE:
                                parsed_url = urlparse(href)
                                if parsed_url.scheme and parsed_url.scheme != 'mailto':
                                    full_url = urljoin(url, href)
                                    if full_url not in self.visited and full_url not in self.queue._queue:
                                        await self.queue.put((full_url, depth + 1))

            except Exception as e:
                print(f"An error occurred: {e}")

    async def worker(self, session):
        # Worker function that fetches URLs from the queue and processes them
        while True:
            url, depth = await self.queue.get()
            await self.fetch(url, session, depth)
            self.queue.task_done()

    async def main(self):
        # Main function that sets up everything and runs the event loop
        headers = {'User-Agent': 'Mozilla/5.0'}
        await self.queue.put((INITIAL_URL, 1))
        num_workers = int(os.cpu_count() * NUM_WORKERS_MULTIPLIER)
        connector = aiohttp.TCPConnector(limit_per_host=TCP_CONNECTOR_LIMIT_PER_HOST)
        async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
            tasks = []
            for _ in range(num_workers):
                task = asyncio.create_task(self.worker(session))
                tasks.append(task)

            html_processor_task = asyncio.create_task(self.html_processor())

            await self.queue.join()
            await self.html_processing_queue.join()

            for task in tasks:
                task.cancel()

            html_processor_task.cancel()

        await self.save_to_file()


if __name__ == "__main__":
    scraper = WebScraper()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(scraper.main())
