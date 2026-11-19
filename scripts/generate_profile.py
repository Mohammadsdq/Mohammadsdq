
#!/usr/bin/env python3
"""Fetch public GitHub data and generate animated SVG profile cards."""

from __future__ import annotations

import base64
import json
import os
import sys
import urllib.error
import urllib.request
import xml.sax.saxutils as xml

from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path


# --------------------------------------------------
# Configuration
# --------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]
CARDS = ROOT / "cards"
DATA = ROOT / "data"

USERNAME = os.getenv("GITHUB_USERNAME", "Mohammadsdq")
TOKEN = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")

URL = "https://api.github.com/graphql"
MAX_REPOSITORIES_TO_SCAN = 1000

P = {
    "bg": "#0B1220",
    "panel": "#111C2E",
    "alt": "#16243A",
    "border": "#263750",
    "text": "#F1F5F9",
    "muted": "#9AAAC0",
    "blue": "#60A5FA",
    "cyan": "#22D3EE",
    "pink": "#F472B6",
    "yellow": "#FBBF24",
    "green": "#34D399",
}


# --------------------------------------------------
# Helpers
# --------------------------------------------------

def esc(value):
    return xml.escape(str(value if value is not None else ""))


def gql(query, variables):
    if not TOKEN:
        raise RuntimeError(
            "GH_TOKEN is missing. Add it as a repository Actions secret."
        )

    payload = json.dumps({
        "query": query,
        "variables": variables
    }).encode()

    req = urllib.request.Request(
        URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
            "Accept": "application/vnd.github+json",
            "User-Agent": "Mohammadsdq-Profile-Generator",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            body = json.loads(res.read().decode())

    except urllib.error.HTTPError as e:
        raise RuntimeError(
            f"GitHub GraphQL HTTP {e.code}: "
            f"{e.read().decode(errors='replace')}"
        ) from e

    except urllib.error.URLError as e:
        raise RuntimeError(
            f"Could not connect to GitHub: {e}"
        ) from e

    if body.get("errors"):
        raise RuntimeError(
            "GraphQL: " + "; ".join(
                x.get("message", "error")
                for x in body["errors"]
            )
        )

    return body["data"]


def fetch_avatar_data_uri(avatar_url):
    """
    Download the GitHub avatar and convert it to a Base64 data URI.
    This allows the avatar to be embedded directly in hero.svg.
    """

    if not avatar_url:
        return None

    try:
        req = urllib.request.Request(
            avatar_url,
            headers={
                "User-Agent": "Mohammadsdq-Profile-Generator",
                "Accept": "image/*",
            },
        )

        with urllib.request.urlopen(req, timeout=20) as response:
            image_bytes = response.read(2_000_000)
            content_type = response.headers.get_content_type()

        if not content_type.startswith("image/"):
            print("Avatar URL did not return an image.")
            return None

        encoded = base64.b64encode(image_bytes).decode("ascii")

        return f"data:{content_type};base64,{encoded}"

    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        print(f"Could not download avatar: {exc}")
        return None


def save(name, svg):
    CARDS.mkdir(exist_ok=True)
    (CARDS / name).write_text(svg, encoding="utf-8")


# --------------------------------------------------
# GitHub API
# --------------------------------------------------

def fetch_user():
    today = datetime.now(timezone.utc).date()
    start = today - timedelta(days=364)

    query = "\n".join([
        "query Profile($login:String!,$from:DateTime!,$to:DateTime!){",
        " user(login:$login){ login name bio avatarUrl url createdAt",
        " followers{totalCount} following{totalCount}",
        " repositories(ownerAffiliations:OWNER,privacy:PUBLIC,isFork:false,first:1){totalCount}",
        " contributionsCollection(from:$from,to:$to){ contributionCalendar{ totalContributions",
        " weeks{ contributionDays{ date contributionCount color weekday } } } }",
        " } }",
    ])

    data = gql(query, {
        "login": USERNAME,
        "from": f"{start.isoformat()}T00:00:00Z",
        "to": f"{today.isoformat()}T23:59:59Z",
    })

    user = data.get("user")

    if not user:
        raise RuntimeError(
            f"GitHub user '{USERNAME}' was not found."
        )

    return user, start, today


def fetch_repositories():
    query = "\n".join([
        "query Repositories($login:String!,$after:String){ user(login:$login){",
        " repositories(ownerAffiliations:OWNER,privacy:PUBLIC,isFork:false,first:100,after:$after,",
        " orderBy:{field:STARGAZERS,direction:DESC}){ pageInfo{hasNextPage endCursor}",
        " nodes{name description url stargazerCount forkCount primaryLanguage{name color}}",
        " } } }",
    ])

    items = []
    cursor = None

    while len(items) < MAX_REPOSITORIES_TO_SCAN:
        conn = gql(query, {
            "login": USERNAME,
            "after": cursor,
        })["user"]["repositories"]

        items.extend(conn["nodes"])

        page = conn["pageInfo"]

        if not page["hasNextPage"] or not page["endCursor"]:
            break

        cursor = page["endCursor"]

    return items[:MAX_REPOSITORIES_TO_SCAN]


# --------------------------------------------------
# SVG Base
# --------------------------------------------------

def start_svg(width, height, title):
    return f"""<svg xmlns="http://www.w3.org/2000/svg"
width="{width}"
height="{height}"
viewBox="0 0 {width} {height}"
role="img"
aria-label="{esc(title)}">

<defs>

    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0" stop-color="{P['bg']}"/>
        <stop offset="1" stop-color="{P['panel']}"/>
    </linearGradient>

    <linearGradient id="accent">
        <stop offset="0" stop-color="{P['blue']}"/>
        <stop offset=".55" stop-color="{P['cyan']}"/>
        <stop offset="1" stop-color="{P['pink']}"/>
    </linearGradient>

    <style>
        text {{
            font-family: Inter, 'Segoe UI', Arial, sans-serif;
        }}

        .heading {{
            font-size: 23px;
            font-weight: 700;
            fill: {P['text']};
        }}

        .label {{
            font-size: 12px;
            font-weight: 600;
            letter-spacing: 2px;
            fill: {P['muted']};
        }}

        .value {{
            font-size: 30px;
            font-weight: 750;
            fill: {P['text']};
        }}

        .small {{
            font-size: 13px;
            fill: {P['muted']};
        }}

        .glow {{
            animation: glow 4s ease-in-out infinite;
        }}

        .sweep {{
            animation: sweep 7s ease-in-out infinite;
        }}

        @keyframes glow {{
            0%, 100% {{ opacity: .35; }}
            50% {{ opacity: .9; }}
        }}

        @keyframes sweep {{
            0%, 65% {{
                transform: translateX(-260px);
                opacity: 0;
            }}
            75% {{ opacity: .75; }}
            100% {{
                transform: translateX(1200px);
                opacity: 0;
            }}
        }}

        @media(prefers-reduced-motion:reduce) {{
            *, *::before, *::after {{
                animation: none !important;
            }}
        }}
    </style>

</defs>

<rect
    x="1"
    y="1"
    width="{width-2}"
    height="{height-2}"
    rx="20"
    fill="url(#bg)"
    stroke="{P['border']}"
/>

"""


def end_svg():
    return "</svg>"


# --------------------------------------------------
# Hero Card - Animated GitHub Avatar
# --------------------------------------------------

def hero(user):
    name = user.get("name") or user["login"]

    bio = (
        user.get("bio")
        or "Learning, building and growing as a backend developer."
    )

    # Download the real GitHub avatar
    avatar = fetch_avatar_data_uri(user.get("avatarUrl"))

    s = start_svg(
        1000,
        250,
        f"{name} GitHub profile"
    )

    s += """
    <defs>
        <clipPath id="avatarClip">
            <circle cx="865" cy="124" r="48"/>
        </clipPath>

        <linearGradient id="avatarBorder">
            <stop offset="0%" stop-color="#60A5FA"/>
            <stop offset="50%" stop-color="#22D3EE"/>
            <stop offset="100%" stop-color="#F472B6"/>
        </linearGradient>
    </defs>
    """

    # Animated background glow
    s += f"""
    <circle
        cx="865"
        cy="124"
        r="92"
        fill="{P['blue']}"
        opacity=".10"
        class="glow"
    />

    <circle
        cx="865"
        cy="124"
        r="76"
        fill="none"
        stroke="{P['cyan']}"
        stroke-width="1"
        opacity=".3"
    />

    <circle
        cx="865"
        cy="124"
        r="65"
        fill="none"
        stroke="{P['cyan']}"
        stroke-opacity=".7"
        stroke-width="1.5"
        stroke-dasharray="4 7"
    >
        <animateTransform
            attributeName="transform"
            type="rotate"
            from="0 865 124"
            to="360 865 124"
            dur="18s"
            repeatCount="indefinite"
        />
    </circle>

    <circle
        cx="865"
        cy="124"
        r="57"
        fill="none"
        stroke="{P['pink']}"
        stroke-opacity=".8"
        stroke-width="2"
        stroke-dasharray="45 20 10 20"
    >
        <animateTransform
            attributeName="transform"
            type="rotate"
            from="360 865 124"
            to="0 865 124"
            dur="12s"
            repeatCount="indefinite"
        />
    </circle>
    """

    # Real avatar
    if avatar:
        s += f"""
        <g>
            <circle
                cx="865"
                cy="124"
                r="52"
                fill="none"
                stroke="url(#avatarBorder)"
                stroke-width="4"
            />

            <image
                href="{avatar}"
                x="817"
                y="76"
                width="96"
                height="96"
                preserveAspectRatio="xMidYMid slice"
                clip-path="url(#avatarClip)"
            />

            <animateTransform
                attributeName="transform"
                type="translate"
                values="0 0; 0 -4; 0 0"
                dur="5s"
                repeatCount="indefinite"
            />
        </g>
        """
    else:
        s += f"""
        <circle
            cx="865"
            cy="124"
            r="48"
            fill="{P['alt']}"
            stroke="url(#avatarBorder)"
            stroke-width="4"
        />

        <text
            x="865"
            y="134"
            text-anchor="middle"
            font-size="30"
            fill="{P['text']}"
        >?</text>
        """

    # Hero text
    s += f"""
    <text x="42" y="52" class="label">
        HELLO, I'M
    </text>

    <text
        x="42"
        y="112"
        font-size="43"
        font-weight="750"
        fill="{P['text']}"
    >{esc(name)}</text>

    <text
        x="44"
        y="151"
        font-size="18"
        fill="{P['cyan']}"
    >
        JavaScript · Node.js · Backend Development
    </text>

    <text
        x="44"
        y="184"
        font-size="15"
        fill="{P['muted']}"
    >{esc(bio[:90])}</text>

    <text
        x="44"
        y="218"
        font-size="12"
        fill="{P['muted']}"
    >@{esc(user['login'])} · github.com/{esc(user['login'])}</text>

    <rect
        class="sweep"
        x="0"
        y="0"
        width="100"
        height="250"
        fill="url(#accent)"
        opacity=".12"
    />
    """

    save("hero.svg", s + end_svg())


# --------------------------------------------------
# Statistics Card
# --------------------------------------------------

def stats(user, cal, repos):
    vals = [
        (
            "PUBLIC REPOS",
            user["repositories"]["totalCount"],
            P["blue"]
        ),
        (
            "FOLLOWERS",
            user["followers"]["totalCount"],
            P["pink"]
        ),
        (
            "STARS EARNED",
            sum(r["stargazerCount"] for r in repos),
            P["yellow"]
        ),
        (
            "CONTRIBUTIONS · 1Y",
            cal["totalContributions"],
            P["green"]
        ),
    ]

    s = start_svg(1000, 178, "GitHub statistics")

    s += '<text x="30" y="39" class="heading">GitHub at a glance</text>'

    for i, (label, val, color) in enumerate(vals):
        x = 30 + i * 242

        s += f"""
        <rect
            x="{x}"
            y="58"
            width="220"
            height="91"
            rx="13"
            fill="{P['alt']}"
            stroke="{P['border']}"
        />

        <rect
            x="{x}"
            y="58"
            width="220"
            height="3"
            rx="1.5"
            fill="{color}"
        />

        <text
            x="{x+16}"
            y="88"
            class="label"
        >{esc(label)}</text>

        <text
            x="{x+16}"
            y="128"
            class="value"
        >{val:,}</text>
        """

    s += f"""
    <text x="30" y="166" class="small">
        Public non-fork repositories scanned: {len(repos)}
        · Public forks received:
        {sum(r['forkCount'] for r in repos):,}
    </text>
    """

    save("stats.svg", s + end_svg())


# --------------------------------------------------
# Contribution Activity Card
# --------------------------------------------------

def activity(cal):
    weeks = cal["weeks"][-53:]

    s = start_svg(
        1000,
        224,
        "GitHub contribution calendar"
    )

    s += f"""
    <text x="28" y="38" class="heading">
        365 days of consistency
    </text>

    <text x="28" y="61" class="small">
        {cal['totalContributions']:,} contributions in the last year
    </text>
    """

    gx, gy, cell, gap = 30, 82, 11, 4

    for wi, week in enumerate(weeks):
        for day in week["contributionDays"]:
            x = gx + wi * (cell + gap)
            y = gy + int(day["weekday"]) * (cell + gap)

            s += f"""
            <rect
                x="{x}"
                y="{y}"
                width="{cell}"
                height="{cell}"
                rx="2.5"
                fill="{esc(day.get('color') or '#17243A')}"
            >
                <title>
                    {esc(day['date'])}:
                    {int(day['contributionCount'])} contributions
                </title>
            </rect>
            """

    s += '<text x="30" y="207" class="small">Less</text>'

    for i, c in enumerate([
        "#161F2E",
        "#0E4429",
        "#006D32",
        "#26A641",
        "#39D353"
    ]):
        s += f"""
        <rect
            x="{75+i*18}"
            y="196"
            width="11"
            height="11"
            rx="2"
            fill="{c}"
        />
        """

    s += '<text x="180" y="207" class="small">More</text>'

    save("activity.svg", s + end_svg())


# --------------------------------------------------
# Programming Languages Card
# --------------------------------------------------

def languages(repos):
    counts = Counter()
    colors = {}

    for r in repos:
        lang = (r.get("primaryLanguage") or {}).get("name")

        if lang:
            counts[lang] += 1
            colors[lang] = (
                (r.get("primaryLanguage") or {}).get("color")
                or P["blue"]
            )

    top = counts.most_common(7)
    total = sum(counts.values())

    s = start_svg(
        1000,
        230,
        "Most used repository languages"
    )

    s += """
    <text x="30" y="40" class="heading">
        Languages across public repositories
    </text>
    """

    if not top:
        s += """
        <text x="30" y="95" class="small">
            No primary language data available yet.
        </text>
        """

    else:
        cursor = 30

        for lang, count in top:
            portion = count / total
            width = max(2, 930 * portion)
            color = colors.get(lang, P["blue"])

            s += f"""
            <rect
                x="{cursor:.1f}"
                y="72"
                width="{width:.1f}"
                height="16"
                fill="{esc(color)}"
            />
            """

            cursor += width

        for i, (lang, count) in enumerate(top):
            x = 32 + (i % 4) * 240
            y = 128 + (i // 4) * 42

            s += f"""
            <circle
                cx="{x+5}"
                cy="{y-4}"
                r="5"
                fill="{esc(colors.get(lang, P['blue']))}"
            />

            <text
                x="{x+18}"
                y="{y}"
                font-size="14"
                font-weight="600"
                fill="{P['text']}"
            >{esc(lang)}</text>

            <text
                x="{x+18}"
                y="{y+17}"
                class="small"
            >{count/total*100:.1f}% · {count} repos</text>
            """

    s += """
    <text x="30" y="213" class="small">
        Based on primary language of scanned public repositories;
        not coding time.
    </text>
    """

    save("languages.svg", s + end_svg())


# --------------------------------------------------
# Featured Repositories Card
# --------------------------------------------------

def repositories(repos):
    featured = sorted(
        repos,
        key=lambda r: (
            r["stargazerCount"],
            r["forkCount"]
        ),
        reverse=True
    )[:6]

    s = start_svg(
        1000,
        100 + max(1, len(featured)) * 65,
        "Featured public repositories"
    )

    s += """
    <text x="30" y="40" class="heading">
        Featured repositories
    </text>
    """

    if not featured:
        s += """
        <text x="30" y="90" class="small">
            No public repositories found yet.
        </text>
        """

    for i, r in enumerate(featured):
        y = 72 + i * 65

        lang = (
            (r.get("primaryLanguage") or {}).get("name")
            or "—"
        )

        desc = (
            r.get("description")
            or "No description provided"
        ).replace("\n", " ")

        if len(desc) > 86:
            desc = desc[:83] + "..."

        s += f"""
        <a href="{esc(r['url'])}">
            <rect
                x="26"
                y="{y-19}"
                width="948"
                height="55"
                rx="10"
                fill="{P['alt']}"
                stroke="{P['border']}"
            />

            <text
                x="44"
                y="{y+3}"
                font-size="16"
                font-weight="700"
                fill="{P['blue']}"
            >{esc(r['name'])}</text>

            <text
                x="44"
                y="{y+22}"
                font-size="12"
                fill="{P['muted']}"
            >{esc(desc)}</text>

            <text
                x="810"
                y="{y+4}"
                font-size="12"
                fill="{P['text']}"
            >★ {r['stargazerCount']} · Forks {r['forkCount']}</text>

            <text
                x="810"
                y="{y+22}"
                font-size="11"
                fill="{P['muted']}"
            >{esc(lang)}</text>
        </a>
        """

    save("repositories.svg", s + end_svg())


# --------------------------------------------------
# Main
# --------------------------------------------------

def main():
    CARDS.mkdir(exist_ok=True)
    DATA.mkdir(exist_ok=True)

    print("Fetching GitHub user data...")

    user, start, today = fetch_user()

    print("Fetching repositories...")

    repos = fetch_repositories()

    cal = user["contributionsCollection"]["contributionCalendar"]

    snapshot = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "username": user["login"],

        "period": {
            "from": start.isoformat(),
            "to": today.isoformat(),
        },

        "public_repository_count":
            user["repositories"]["totalCount"],

        "scanned_repository_count": len(repos),

        "followers":
            user["followers"]["totalCount"],

        "following":
            user["following"]["totalCount"],

        "total_contributions":
            cal["totalContributions"],

        "repositories": repos,

        "contribution_calendar": cal,
    }

    (DATA / "github_stats.json").write_text(
        json.dumps(
            snapshot,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    print("Generating SVG cards...")

    hero(user)
    stats(user, cal, repos)
    activity(cal)
    languages(repos)
    repositories(repos)

    print(
        f"Generated cards for @{user['login']}: "
        f"{cal['totalContributions']} contributions, "
        f"{len(repos)} repos scanned."
    )


if __name__ == "__main__":
    try:
        main()

    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
