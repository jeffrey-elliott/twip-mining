# Pass 01 - Discover Transcripts

Input: the Club Floyd index and a couple example urls

Output: `data/manifest.jsonl`

For example:

```
{
  "id": "2025-01-26-no-more",
  "source_url": "https://allthingsjacq.com/intfic_clubfloyd_20250105.html",
  "year": 2025,
  "played_date": "2025-01-26",
  "page_title": "ClubFloyd - January 26, 2025 - No More by Tabitha",
  "games": [
    {
      "title": "No More",
      "author": "Tabitha"
    }
  ],
  "raw_path": "data/raw/2025/2025-01-26-no-more/source.html",
  "status": "discovered"
}
```

Rules:
- Discover by following links from the index page: https://allthingsjacq.com/interactive_fiction.html
- Include links matching ClubFloyd/NightFloyd transcript patterns.
- Do not assume all pages use one URL pattern.
- Do not infer played dates from URL if page text provides a date.
- Preserve source_url always.