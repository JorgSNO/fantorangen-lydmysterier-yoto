from feedgen.feed import FeedGenerator

fg = FeedGenerator()

fg.title("Fantorangens lydmysterier")
fg.description("Privat Yoto-feed")
fg.link(href="https://radio.nrk.no")

episode_url = "https://example.com/audio.mp3"

fe = fg.add_entry()
fe.title("Test episode")
fe.enclosure(
    episode_url,
    1000,
    "audio/mpeg"
)

fg.rss_file("podcast.xml")