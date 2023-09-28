import asyncio
import aiohttp
from urllib.parse import urljoin
import os
from bs4 import BeautifulSoup
import glob
import json

class WebScraper:
    def __init__(self):
        self.MAX_QUEUE_SIZE = 500
        self.DEPTH_LIMIT = None
        self.FILE_NAME = "clean_scraped_data{}.txt"
        self.VISITED_URLS_FILE = "visited_urls.json"
        self.BUFFER_SIZE = 50
        self.INITIAL_URL = "https://github.com/Turbo1337GS/"
        self.NUM_WORKERS_MULTIPLIER = 16
        self.TCP_CONNECTOR_LIMIT_PER_HOST = 400
        self.MAX_FILE_SIZE_MB = 1000
        self.START_TOKEN = "<-----StartText----->"
        self.END_TOKEN = "<-----EndText----->"

        self.load_visited_urls()
        self.queue = asyncio.Queue()
        self.html_processing_queue = asyncio.Queue()
        self.unique_texts = set()
        self.buffered_texts = []
        self.semaphore = asyncio.Semaphore(500)
        self.current_file_index = 0

    def load_visited_urls(self):
        try:
            with open(self.VISITED_URLS_FILE, "r") as f:
                self.visited = set(json.load(f))
                print("U must change init url ;)\n")
        except FileNotFoundError:
            self.visited = set()

    def save_visited_urls(self):
        with open(self.VISITED_URLS_FILE, "w") as f:
            json.dump(list(self.visited), f)

    async def save_to_file(self):
        current_file_name = self.FILE_NAME.format(self.current_file_index)
        with open(current_file_name, 'a', encoding='utf-8') as f:
            for text in self.buffered_texts:
                f.write(self.START_TOKEN)
                f.write(text)
                f.write(self.END_TOKEN)
                f.write('\n')
        self.buffered_texts.clear()

        folder_size = self.get_folder_size_in_MB(".")
        
        if folder_size >= self.MAX_FILE_SIZE_MB:
            self.current_file_index += 1

        self.save_visited_urls()

        print(f"(Visited: {len(self.visited)} articles, "
              f"Folder size: {folder_size:.2f} MB, "
              f"Queue size: {self.queue.qsize()}, "
              f"Unique texts: {len(self.unique_texts)})")

    def get_folder_size_in_MB(self, folder_path):
        size = 0
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                full_path = os.path.join(root, file)
                size += os.path.getsize(full_path)
        size_in_MB = size / (1024 * 1024)
        return size_in_MB

    async def process_html(self, text):
        if not text.strip():
            return

        soup = BeautifulSoup(text, 'html.parser')
        cleaned_text = soup.text.strip()

        if len(cleaned_text) > 20:
            cleaned_content = ' '.join(cleaned_text.split())
            if cleaned_content not in self.unique_texts:
                self.unique_texts.add(cleaned_content)
                self.buffered_texts.append(cleaned_content)

                if len(self.buffered_texts) >= self.BUFFER_SIZE:
                    await self.save_to_file()

    async def html_processor(self):
        while True:
            text = await self.html_processing_queue.get()
            await self.process_html(text)
            self.html_processing_queue.task_done()

    async def fetch(self, url, session, depth):
        async with self.semaphore:
            if (self.DEPTH_LIMIT is not None and depth > self.DEPTH_LIMIT) or url in self.visited:
                return

            if not url.startswith("http"):
                return

            self.visited.add(url)
            try:
                async with session.get(url, ssl=False) as response:
                    if response.status != 200:
                        return

                    if 'text/html' not in response.headers.get('content-type', ''):
                        return

                    text = await response.text(errors='replace')
                    await self.html_processing_queue.put(text)

                    for link in BeautifulSoup(text, 'html.parser').find_all('a'):
                        href = link.get('href')
                        if href and "javascript:" not in href:
                            full_url = urljoin(url, href)
                            if full_url not in self.visited:
                                if self.queue.qsize() < self.MAX_QUEUE_SIZE:
                                    await self.queue.put((full_url, depth + 1))

            except Exception as e:
                print(f"An error occurred: {e}")

    async def worker(self, session):
        while True:
            url, depth = await self.queue.get()
            await self.fetch(url, session, depth)
            self.queue.task_done()

    async def main(self):
        headers = {'User-Agent': 'Mozilla/5.0'}
        await self.queue.put((self.INITIAL_URL, 1))
        num_workers = int(os.cpu_count() * self.NUM_WORKERS_MULTIPLIER)
        connector = aiohttp.TCPConnector(limit_per_host=self.TCP_CONNECTOR_LIMIT_PER_HOST)
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
