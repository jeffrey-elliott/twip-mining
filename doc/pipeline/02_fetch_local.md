# Pass 02 - Fetch Local

Fetch each manifest URL politely.

Requirements:
- Custom user-agent.
- One request at a time.
- Delay between requests.
- Save raw HTML exactly.
- Save SHA-256.
- Skip unchanged files unless forced.
- Record fetch timestamp.
- Never overwrite without preserving enough metadata to know what changed.

Check `robots.txt` and fetch politely.
