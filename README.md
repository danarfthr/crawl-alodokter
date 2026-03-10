# Alodokter Scraper

A simple Python script to scrape articles from Alodokter.com using the `crawl4ai` library.

## What it does
The script (`scraper.py`) navigates through specific Alodokter categories (`kesehatan`, `keluarga`, and `hidup-sehat`), collects article links, and extracts the following information into a CSV file (`alodokter_articles.csv`):

- **Judul**: The article's title.
- **Isi**: The article's main content formatted as markdown.
- **Ringkasan**: Left blank (for future AI-generated summaries).
- **Referensi**: Any references listed at the end of the article.
- **Tanggal Rilis**: The date the article was last updated.
- **Peninjau**: The reviewer or author's name.
- **URL**: The link to the article.

## Usage

Ensure you have your environment set up and the necessary dependencies installed (`uv sync`).

To run the scraper and collect all possible articles:
```bash
uv run python scraper.py
```

### Arguments

* **`--limit <N>`**: Limits the number of articles actually scraped. Useful if you only want to retrieve a certain amount.
  ```bash
  uv run python scraper.py --limit 10
  ```

* **`--test`**: A quick test flag that restricts the scrape to only the first 2 discovered articles. This is useful for testing without hitting rate limits.
  ```bash
  uv run python scraper.py --test
  ```
