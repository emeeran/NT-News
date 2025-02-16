from datetime import datetime


def get_news_sources():
    zdnet_published = "2025-02-15T08:00:00Z"
    dt = datetime.strptime(zdnet_published, "%Y-%m-%dT%H:%M:%SZ")
    display_date = dt.strftime("%B %d, %Y, %H:%M UTC")

    irish_sun_published = "2025-02-16T08:00:00Z"
    dt_irish_sun = datetime.strptime(irish_sun_published, "%Y-%m-%dT%H:%M:%SZ")
    short_irish_sun_display = dt_irish_sun.strftime("%b %d, %Y %H:%M UTC")

    the_guardian_published = "2025-02-16T09:00:05Z"
    dt_guardian = datetime.strptime(the_guardian_published, "%Y-%m-%dT%H:%M:%SZ")
    guardian_display = dt_guardian.strftime("%B %d, %Y, %H:%M UTC")

    return [
        {
            "name": "ZDNet",
            "url": "https://www.zdnet.com",
            "published": zdnet_published,
            "display_date": display_date,
        },
        {
            "name": "The Irish Sun",
            "url": "https://www.thesun.ie",
            "published": irish_sun_published,
            "display_date": short_irish_sun_display,
        },
        {
            "name": "The Guardian",
            "url": "https://www.theguardian.com",
            "published": the_guardian_published,
            "display_date": guardian_display,
        },
    ]
