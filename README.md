# Uni Finder

Search universities by **name** or **country** and view their websites.

Built with **Python FastAPI** using the free [Hipolabs Universities API](https://github.com/Hipo/university-domains-list-api).

## Features

- Search by university name and/or country
- Show official website links from the API
- JSON API endpoint for programmatic use
- Automatic fallback to the official Hipolabs GitHub dataset if the live API is slow or fails
- Simple web UI

## Tech stack

- FastAPI
- Uvicorn
- httpx
- Jinja2 templates

## Project structure

```text
Uni Finder/
├── app/
│   ├── main.py          # Routes (UI + API)
│   ├── services.py      # Hipolabs API + backup search
│   └── schemas.py       # Response models
├── templates/
│   └── index.html       # Search page
├── static/
│   └── style.css
├── requirements.txt
└── README.md
```

## Setup

```bash
python -m venv .venv
```

**Windows (PowerShell):**

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**macOS / Linux:**

```bash
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open: [http://127.0.0.1:8000](http://127.0.0.1:8000)

## Usage

### Web UI

1. Open the home page
2. Enter a university name and/or country
3. Click **Search**

Examples that work with Hipolabs data:

- Name: `Lahore` · Country: `Pakistan`
- Name: `LUMS` · Country: `Pakistan`
- Name: `Oxford`
- Country only: `Pakistan`

> Note: Results only include universities present in the Hipolabs dataset. If a university is missing from that API, it will not appear here.

### JSON API

```http
GET /api/universities?name=Lahore&country=Pakistan
```

Example response:

```json
{
  "source": "primary",
  "count": 1,
  "query": { "name": "Lahore", "country": "Pakistan" },
  "results": [
    {
      "name": "Lahore University of Management Sciences",
      "country": "Pakistan",
      "web_pages": ["http://www.lums.edu.pk/"],
      "domains": ["lums.edu.pk"]
    }
  ]
}
```

### Other endpoints

| Endpoint | Description |
|----------|-------------|
| `/` | Search UI |
| `/api/universities` | JSON search |
| `/health` | Health check |
| `/docs` | Swagger UI |

## Data source

- Primary: `http://universities.hipolabs.com/search`
- Backup (same official list): [world_universities_and_domains.json](https://github.com/Hipo/university-domains-list/blob/master/world_universities_and_domains.json)

No API key required.

## License

Student / learning project for PSEB Module 1.
