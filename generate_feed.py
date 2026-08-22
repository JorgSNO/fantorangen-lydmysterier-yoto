import csv
import hashlib
import html
import urllib.request
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime


CSV_FILE = "episodes.csv"
OUTPUT_FILE = "podcast.xml"

FEED_TITLE = "Fantorangens lydmysterier"
WEBSITE_URL = (
    "https://jorgsno.github.io/"
    "fantorangen-lydmysterier-yoto/"
)


def get_file_size(url):
    """
    Retrieve the real MP3 size without downloading the full episode.
    Falls back to 1 if the CDN does not expose the total size.
    """
    try:
        request = urllib.request.Request(
            url,
            headers={
                "Range": "bytes=0-0",
                "User-Agent": "Fantorangen-Yoto-RSS/1.0",
            },
        )

        with urllib.request.urlopen(request, timeout=30) as response:
            content_range = response.headers.get("Content-Range", "")

            if "/" in content_range:
                total = content_range.rsplit("/", 1)[-1]

                if total.isdigit():
                    return total

            content_length = response.headers.get("Content-Length")

            if content_length and content_length.isdigit():
                return content_length

    except Exception as error:
        print(f"Warning: Could not retrieve file size: {error}")

    return "1"


def check_url(url):
    """
    Confirm that the URL returns an MP3 successfully.
    """
    try:
        request = urllib.request.Request(
            url,
            headers={
                "Range": "bytes=0-0",
                "User-Agent": "Fantorangen-Yoto-RSS/1.0",
            },
        )

        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status in (200, 206)

    except Exception as error:
        print(f"ERROR: URL failed: {url}")
        print(f"Reason: {error}")
        return False


def read_episodes():
    episodes = []

    with open(
        CSV_FILE,
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(file)

        expected_columns = {"title", "url"}
        actual_columns = set(reader.fieldnames or [])

        if not expected_columns.issubset(actual_columns):
            raise ValueError(
                "episodes.csv must contain the columns title,url. "
                f"Found: {reader.fieldnames}"
            )

        for row_number, row in enumerate(reader, start=2):
            title = (row.get("title") or "").strip()
            url = (row.get("url") or "").strip()

            if not title and not url:
                continue

            if not title:
                raise ValueError(
                    f"Missing title on CSV row {row_number}"
                )

            if not url:
                raise ValueError(
                    f"Missing URL on CSV row {row_number}"
                )

            episodes.append(
                {
                    "title": title,
                    "url": url,
                }
            )

    if not episodes:
        raise ValueError("No episodes found in episodes.csv")

    return episodes


def create_guid(url):
    return hashlib.sha256(url.encode("utf-8")).hexdigest()


def build_feed(episodes):
    now = datetime.now(timezone.utc)

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0" '
        'xmlns:atom="http://www.w3.org/2005/Atom">',
        "  <channel>",
        f"    <title>{html.escape(FEED_TITLE)}</title>",
        f"    <link>{html.escape(WEBSITE_URL)}</link>",
        "    <description>"
        "Fantorangen og Pivi jakter på mystiske lyder."
        "</description>",
        "    <language>nb-NO</language>",
        f"    <lastBuildDate>{format_datetime(now)}</lastBuildDate>",
        (
            '    {html.escape(WEBSITE_URL)}podcast.xml'
        ),
    ]

    valid_count = 0

    for index, episode in enumerate(episodes):
        title = episode["title"]
        url = episode["url"]

        print(f"Checking {index + 1}/{len(episodes)}: {title}")

        if not check_url(url):
            print(f"Skipping unavailable episode: {title}")
            continue

        file_size = get_file_size(url)
        guid = create_guid(url)
        publication_date = now - timedelta(minutes=index)

        lines.extend(
            [
                "    <item>",
                f"      <title>{html.escape(title)}</title>",
                (
                    "      <description>"
                    f"Episode av Fantorangens lydmysterier: "
                    f"{html.escape(title)}"
                    "</description>"
                ),
                (
                    '      <guid isPermaLink="false">'
                    f"{guid}"
                    "</guid>"
                ),
                (
                    "      <pubDate>"
                    f"{format_datetime(publication_date)}"
                    "</pubDate>"
                ),
                (
                    '      <enclosure '
                    f'url="{html.escape(url, quote=True)}" '
                    f'length="{file_size}" '
                    'type="audio/mpeg" />'
                ),
                "    </item>",
            ]
        )

        valid_count += 1

    lines.extend(
        [
            "  </channel>",
            "</rss>",
            "",
        ]
    )

    if valid_count == 0:
        raise RuntimeError(
            "No working MP3 URLs were found. "
            "podcast.xml was not updated."
        )

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
        newline="\n",
    ) as output:
        output.write("\n".join(lines))

    print(
        f"Generated {OUTPUT_FILE} with "
        f"{valid_count} working episodes."
    )

    if valid_count != len(episodes):
        print(
            f"Warning: {len(episodes) - valid_count} "
            "episodes were skipped."
        )


def main():
    episodes = read_episodes()

    print(f"Loaded {len(episodes)} episode records.")

    build_feed(episodes)


if __name__ == "__main__":
    main()
``
