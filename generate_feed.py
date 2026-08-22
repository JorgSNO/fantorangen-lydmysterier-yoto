import csv

with open("episodes.csv", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

rss = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
<title>Fantorangens lydmysterier</title>
<link>https://jorgsno.github.io/fantorangen-lydmysterier-yoto/</link>
<description>Fantorangen på Yoto</description>
<language>nb-NO</language>
"""

for row in rows:
    episode_id = row["id"]
    title = row["title"]

    mp3 = (
        "https://nrk-pod-pd.telenorcdn.net/"
        "podkast/podcastpublisher_prod/"
        "fantorangens_lydmysterier/"
        f"{episode_id}_1_ID192MP3.mp3"
    )

    rss += f"""
<item>
<title>{title}</title>
<guid>{episode_id}</guid>
<enclosure url="{mp3}" length="1" type="audio/mpeg"/>
</item>
"""

rss += """
</channel>
</rss>
"""

with open("podcast.xml", "w", encoding="utf-8") as f:
    f.write(rss)

print(f"Generated {len(rows)} episodes")
