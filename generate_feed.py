import csv
import sys
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, ElementTree, indent

import requests


EPISODES_FILE = Path("episodes.csv")
OUTPUT_FILE = Path("podcast.xml")

WEBSITE_URL = (
    "https://jorgsno.github.io/"
    "fantorangen-lydmysterier-yoto/"
)

MP3_BASE_URL = (
    "https://nrk-pod-pd.telenorcdn.net/"
    "podkast/podcastpublisher_prod/"
    "fantorangens_lydmysterier/"
)

REQUEST_TIMEOUT = 30


def create_mp3_url(episode_id):
    return (
        f"{MP3_BASE_URL}"
        f"{episode_id}_1_ID192MP3.mp3"
    )


def get_audio_length(mp3_url):
    """
    Ask the NRK CDN for the MP3 file size.

    If the CDN does not return a Content-Length header,
    use 1. Yoto accepts this fallback in the tested feed.
    """
    try:
        response = requests.head(
            mp3_url,
            allow_redirects=True,
            timeout=REQUEST_TIMEOUT,
        )

        if response.status_code == 405:
            response = requests.get(
                mp3_url,
                headers={"Range": "bytes=0-0"},
                stream=True,
                timeout=REQUEST_TIMEOUT,
            )

        response.raise_for_status()

        content_range = response.headers.get("Content-Range", "")
        if "/" in content_range:
            total_size = content_range.rsplit("/", 1)[-1]
            if total_size.isdigit():
                return total_size

        content_length = response.headers.get("Content-Length")
        if content_length and content_length.isdigit():
            return content_length

    except requests.RequestException as error:
        print(
            f"Warning: Could not determine MP3 size: {error}",
            file=sys.stderr,
        )

    return "1"


def validate_mp3(mp3_url):
    """
    Check whether the constructed NRK MP3 URL exists.
    """
    try:
        response = requests.get(
            mp3_url,
            headers={"Range": "bytes=0-0"},
            stream=True,
            timeout=REQUEST_TIMEOUT,
        )

        if response.status_code not in (200, 206):
            print(
                f"Warning: MP3 returned HTTP "
                f"{response.status_code}: {mp3_url}",
                file=sys.stderr,
            )
            return False

        content_type = response.headers.get(
            "Content-Type",
            "",
        ).lower()

        if content_type and "audio" not in content_type:
            print(
                f"Warning: Unexpected content type "
                f"{content_type}: {mp3_url}",
                file=sys.stderr,
            )

        return True

    except requests.RequestException as error:
        print(
            f"Warning: Could not validate {mp3_url}: {error}",
            file=sys.stderr,
        )
        return False


def read_episodes():
    episodes = []

    with EPISODES_FILE.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as csv_file:
        reader = csv.DictReader(csv_file)

        for row_number, row in enumerate(reader, start=2):
            episode_id = row.get("id", "").strip()
            title = row.get("title", "").strip()

            if not episode_id or not title:
                raise ValueError(
                    f"Missing ID or title on CSV row {row_number}"
                )

            episodes.append(
                {
                    "id": episode_id,
                    "title": title,
                }
            )

    if not episodes:
        raise ValueError("episodes.csv contains no episodes")

    return episodes


def build_feed(episodes):
    rss = Element(
        "rss",
        {
            "version": "2.0",
            "xmlns:atom": "http://www.w3.org/2005/Atom",
        },
    )

    channel = SubElement(rss, "channel")

    SubElement(
        channel,
        "title",
    ).text = "Fantorangens lydmysterier"

    SubElement(
        channel,
        "link",
    ).text = WEBSITE_URL

    SubElement(
        channel,
        "description",
    ).text = (
        "Fantorangen og Pivi jakter på mystiske lyder. "
        "Privat podcast-feed for avspilling på Yoto."
    )

    SubElement(
        channel,
        "language",
    ).text = "nb-NO"

    SubElement(
        channel,
        "generator",
    ).text = "GitHub Actions"

    SubElement(
        channel,
        "lastBuildDate",
    ).text = format_datetime(datetime.now(timezone.utc))

    SubElement(
        channel,
        "{http://www.w3.org/2005/Atom}link",
        {
            "href": f"{WEBSITE_URL}podcast.xml",
            "rel": "self",
            "type": "application/rss+xml",
        },
    )

    newest_date = datetime.now(timezone.utc)

    for position, episode in enumerate(episodes):
        episode_id = episode["id"]
        title = episode["title"]
        mp3_url = create_mp3_url(episode_id)

        print(f"Processing: {title}")
        print(f"MP3: {mp3_url}")

        if not validate_mp3(mp3_url):
            print(
                f"Skipping unavailable episode: {title}",
                file=sys.stderr,
            )
            continue

        audio_length = get_audio_length(mp3_url)

        item = SubElement(channel, "item")

        SubElement(
            item,
            "title",
        ).text = title

        SubElement(
            item,
            "description",
        ).text = (
            f"Episode av Fantorangens lydmysterier: {title}"
        )

        SubElement(
            item,
            "guid",
            {"isPermaLink": "false"},
        ).text = episode_id

        episode_date = newest_date - timedelta(minutes=position)

        SubElement(
            item,
            "pubDate",
        ).text = format_datetime(episode_date)

        SubElement(
            item,
            "enclosure",
            {
                "url": mp3_url,
                "length": audio_length,
                "type": "audio/mpeg",
            },
        )

    indent(rss, space="  ")

    tree = ElementTree(rss)
    tree.write(
        OUTPUT_FILE,
        encoding="utf-8",
        xml_declaration=True,
    )


def main():
    episodes = read_episodes()
    build_feed(episodes)

    print(
        f"Created {OUTPUT_FILE} from "
        f"{len(episodes)} episode records."
    )


if __name__ == "__main__":
    main()
