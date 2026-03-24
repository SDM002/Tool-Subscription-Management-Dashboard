"""
app/tools/alternative_lookup.py  [NEW]

Static knowledge base of free / cheaper alternatives to popular SaaS tools.
Used by the AI assistant's get_alternatives tool call.
"""

ALTERNATIVES_DB: dict[str, list[dict]] = {
    "figma": [
        {"name": "Penpot",   "price": "Free (open source)", "url": "https://penpot.app",        "note": "Best open-source Figma alternative"},
        {"name": "Lunacy",   "price": "Free",                "url": "https://icons8.com/lunacy",  "note": "Windows/Mac, imports Figma files"},
        {"name": "Framer",   "price": "Free tier",           "url": "https://framer.com",         "note": "Great for prototyping"},
    ],
    "notion": [
        {"name": "Obsidian", "price": "Free (local)",        "url": "https://obsidian.md",        "note": "Local-first, markdown"},
        {"name": "AppFlowy", "price": "Free (open source)",  "url": "https://appflowy.io",        "note": "Self-hostable Notion alternative"},
        {"name": "Logseq",   "price": "Free",                "url": "https://logseq.com",         "note": "Graph-based notes"},
        {"name": "Joplin",   "price": "Free (open source)",  "url": "https://joplinapp.org",      "note": "Cross-platform, E2E encrypted"},
    ],
    "slack": [
        {"name": "Discord",      "price": "Free",                "url": "https://discord.com",        "note": "Popular for dev teams"},
        {"name": "Mattermost",   "price": "Free (self-hosted)",  "url": "https://mattermost.com",     "note": "Enterprise open-source"},
        {"name": "Zulip",        "price": "Free (open source)",  "url": "https://zulip.com",          "note": "Threaded conversations"},
        {"name": "Matrix/Element","price":"Free (open source)",  "url": "https://element.io",         "note": "Decentralised, E2E encrypted"},
    ],
    "github": [
        {"name": "GitLab",   "price": "Free tier",           "url": "https://gitlab.com",         "note": "Full DevOps platform, self-hostable"},
        {"name": "Gitea",    "price": "Free (self-hosted)",  "url": "https://gitea.io",           "note": "Lightweight, low resource usage"},
        {"name": "Codeberg", "price": "Free",                "url": "https://codeberg.org",       "note": "Non-profit Gitea hosting"},
    ],
    "jira": [
        {"name": "Linear",   "price": "Free up to 250 issues","url": "https://linear.app",       "note": "Fast and keyboard-driven"},
        {"name": "Plane",    "price": "Free (open source)",  "url": "https://plane.so",           "note": "Self-hostable Jira alternative"},
        {"name": "YouTrack", "price": "Free up to 10 users", "url": "https://jetbrains.com/youtrack","note": "Powerful issue tracker"},
        {"name": "Taiga",    "price": "Free (open source)",  "url": "https://taiga.io",           "note": "Agile project management"},
    ],
    "zoom": [
        {"name": "Google Meet","price":"Free with Google",   "url": "https://meet.google.com",    "note": "No install needed"},
        {"name": "Jitsi Meet","price": "Free (open source)", "url": "https://meet.jit.si",        "note": "No account needed, self-hostable"},
        {"name": "BigBlueButton","price":"Free (self-hosted)","url":"https://bigbluebutton.org",  "note": "Great for education/webinars"},
    ],
    "dropbox": [
        {"name": "Nextcloud","price": "Free (self-hosted)",  "url": "https://nextcloud.com",      "note": "Full cloud suite, self-hostable"},
        {"name": "Mega",     "price": "20 GB free",          "url": "https://mega.io",            "note": "E2E encrypted cloud storage"},
        {"name": "Syncthing","price": "Free (open source)",  "url": "https://syncthing.net",      "note": "P2P sync, no cloud needed"},
    ],
    "grammarly": [
        {"name": "LanguageTool","price":"Free tier",         "url": "https://languagetool.org",   "note": "Open source, self-hostable"},
        {"name": "Hemingway",  "price":"$19.99 one-time",   "url": "https://hemingwayapp.com",   "note": "Readability-focused editor"},
        {"name": "ProWritingAid","price":"Free tier",        "url": "https://prowritingaid.com",  "note": "Deep writing analysis"},
    ],
    "trello": [
        {"name": "Planka",   "price": "Free (self-hosted)",  "url": "https://planka.app",         "note": "Open-source Trello clone"},
        {"name": "Wekan",    "price": "Free (self-hosted)",  "url": "https://wekan.github.io",    "note": "Kanban, self-hostable"},
        {"name": "Focalboard","price":"Free (open source)",  "url": "https://focalboard.com",     "note": "By Mattermost team"},
    ],
    "1password": [
        {"name": "Bitwarden","price": "Free (open source)",  "url": "https://bitwarden.com",      "note": "Best free password manager"},
        {"name": "KeePassXC","price": "Free (local)",        "url": "https://keepassxc.org",      "note": "Local-only, no cloud"},
        {"name": "Vaultwarden","price":"Free (self-hosted)", "url": "https://github.com/dani-garcia/vaultwarden","note": "Self-hosted Bitwarden server"},
    ],
    "loom": [
        {"name": "OBS Studio","price":"Free (open source)",  "url": "https://obsproject.com",     "note": "Full-featured screen recorder"},
        {"name": "Screenity", "price":"Free (Chrome ext)",   "url": "https://screenity.io",       "note": "No account needed"},
        {"name": "Cap",       "price":"Free tier",           "url": "https://cap.so",             "note": "Open-source Loom alternative"},
    ],
    "linear": [
        {"name": "Plane",    "price": "Free (open source)",  "url": "https://plane.so",           "note": "Self-hostable"},
        {"name": "GitLab Issues","price":"Free tier",        "url": "https://gitlab.com",         "note": "Built into GitLab"},
    ],
    "vercel": [
        {"name": "Netlify",  "price": "Free tier",           "url": "https://netlify.com",        "note": "Similar generous free tier"},
        {"name": "Cloudflare Pages","price":"Free tier",     "url": "https://pages.cloudflare.com","note": "Fast global CDN"},
        {"name": "Railway",  "price": "Free tier",           "url": "https://railway.app",        "note": "Great for full-stack apps"},
    ],
}


def lookup_alternatives(tool_name: str) -> dict:
    """
    Find alternatives for a given tool name.
    Does case-insensitive partial matching.
    """
    name_lower = tool_name.lower().strip()

    # Direct key match
    if name_lower in ALTERNATIVES_DB:
        return {
            "tool": tool_name,
            "found": True,
            "alternatives": ALTERNATIVES_DB[name_lower],
        }

    # Partial match (e.g. "GitHub" → "github", "1Password" → "1password")
    for key, alts in ALTERNATIVES_DB.items():
        if key in name_lower or name_lower in key:
            return {
                "tool": tool_name,
                "found": True,
                "alternatives": alts,
            }

    return {
        "tool": tool_name,
        "found": False,
        "alternatives": [],
        "message": (
            f"No specific alternatives found for '{tool_name}' in the knowledge base. "
            "You can search Google for 'open source alternative to " + tool_name + "' "
            "or check https://alternativeto.net"
        ),
    }
