def read_episodes():
    episodes = []

    with EPISODES_FILE.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as csv_file:
        reader = csv.reader(csv_file)

        header = next(reader, None)

        if header != ["id", "title"]:
            raise ValueError(
                f"Expected CSV header ['id', 'title'], found {header}"
            )

        for row_number, row in enumerate(reader, start=2):
            if not row or all(not value.strip() for value in row):
                continue

            if len(row) != 2:
                raise ValueError(
                    f"CSV row {row_number} has {len(row)} columns "
                    f"instead of 2. Content: {row!r}"
                )

            episode_id = row[0].strip()
            title = row[1].strip()

            if not episode_id:
                raise ValueError(
                    f"Missing episode ID on CSV row {row_number}"
                )

            if not title:
                raise ValueError(
                    f"Missing title on CSV row {row_number}"
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
