# GraceBox

**AI-powered email civility firewall** — screens incoming emails for hostile tone and rewrites them with grace before delivery.

> *Where every message arrives with grace.*

## What is GraceBox?

GraceBox sits between senders and your inbox. When someone sends you a hostile or aggressive email, GraceBox detects the tone, rewrites the message to be constructive and respectful, and delivers the civil version to you. Optionally, senders are notified that their message was adjusted.

**Target users:**
- Professionals in high-conflict industries (insurance, real estate, law, consulting)
- Individuals in personal high-conflict situations (co-parenting, family disputes, abusive relationships)

## Features (Phases 1–3)

- **User accounts** with tier-based subscriptions (Free, Personal, Professional, Team)
- **Screened sender management** — add/remove senders, toggle active/notify per sender
- **Email activity log** with pagination, filters, and expandable detail rows
- **Dashboard** with usage stats, progress bars, and sender overview
- **Settings** — tone sensitivity slider, notification preferences, data retention, Gmail connection placeholder
- **Billing page** — tier comparison cards with upgrade/downgrade flow (Stripe integration placeholder)
- **Interactive rewrite demo** — 5 preset example emails across professional and personal conflict scenarios, multi-step AI processing animation, tone gauge, word-level diff highlighting, and sender notification preview card

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Single-page HTML/CSS/JS app with hash routing |
| Backend | Python CGI scripts (5 endpoints) |
| Database | SQLite with WAL mode |
| Typography | DM Serif Display + Plus Jakarta Sans |
| Deployment | Static hosting (S3) with CGI-bin backend |

## Project Structure

```
gracebox/
├── index.html              # Full subscriber dashboard (single-page app)
├── README.md
├── cgi-bin/
│   ├── db.py               # Shared database module (SQLite, helpers, tier config)
│   ├── users.py            # User CRUD (GET/POST/PATCH)
│   ├── senders.py          # Screened sender CRUD (GET/POST/PATCH/DELETE)
│   ├── logs.py             # Email activity log (GET with pagination, POST)
│   └── stats.py            # Dashboard statistics endpoint
```

## API Endpoints

| Endpoint | Methods | Description |
|----------|---------|-------------|
| `/cgi-bin/users.py` | GET, POST, PATCH | User account management |
| `/cgi-bin/senders.py` | GET, POST, PATCH, DELETE | Screened sender CRUD |
| `/cgi-bin/logs.py` | GET, POST | Email activity logging |
| `/cgi-bin/stats.py` | GET | Dashboard statistics |

## Pricing Tiers

| Tier | Price | Senders | Emails/mo |
|------|-------|---------|-----------|
| Free | $0 | 1 | 25 |
| Personal | $9/mo | 10 | 200 |
| Professional | $14/mo | 25 | 500 |
| Team | $12/user/mo | 50 | 1,000 |

## Brand

- **Colors:** Navy (#1B2A4A), Gold (#C9A96E), Warm White (#FAF8F5), Sage (#7A9E7E), Coral (#D4726A)
- **Voice:** Calm, confident, empathic — "executive coach" not "productivity bro"

## Build Phases

- [x] **Phase 1:** Backend API + database + test console
- [x] **Phase 2:** Subscriber dashboard (6-page SPA)
- [x] **Phase 3:** Enhanced demo experience
- [ ] **Phase 4:** Gmail integration (Pub/Sub + OAuth)
- [ ] **Phase 5:** AI rewrite engine (OpenAI/Anthropic)
- [ ] **Phase 6:** Stripe billing integration
- [ ] **Phase 7:** Production hardening + launch

## License

Proprietary — all rights reserved.
