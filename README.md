# Rivo-Drome

Proxy Subsonic che sostituisce Navidrome per ricerca e riproduzione, usando Deezer come fonte metadati e una catena di downloader (torrent + YouTube) per lo streaming on-demand.

## Architettura

```
Client Subsonic (Symfonium, Ultrasonic, ecc.)
       │
       ▼
 ┌─────────────────┐
 │  FastAPI (proxy) │─── /rest/search*, /rest/getArtist*, ecc. → database locale
 │                  │─── /rest/stream, /rest/download        → downloader chain
 │                  │─── /* (tutto il resto)                  → Navidrome (proxy passante)
 └─────────────────┘
```

## Flussi principali

### Ricerca (`/rest/search3.view`, ecc.)
1. Il client chiama l'endpoint Subsonic
2. Rivo-Drome interroga l'**API pubblica di Deezer**
3. I risultati (artisti, album, tracce) vengono salvati su **MariaDB** con ID auto-increment
4. La risposta è formattata nel formato Subsonic standard, usando gli ID locali

### Streaming (`/rest/stream.view`)
1. Il client richiede una traccia via ID
2. Se il file esiste già su disco → restituito immediatamente
3. Altrimenti si attiva la **catena di downloader** (Chain of Responsibility):
   - **TorrentDownloader**: cerca su Jackett, avvia su TorrServer, scarica il file audio
   - **YoutubeDownloader** (fallback): scarica via yt-dlp
4. Il file viene salvato, il DB aggiornato, e lo stream servito al client

### Proxy passante
Tutte le altre richieste Subsonic (ping, getPlaylists, scrobble, ecc.) vengono inoltrate a Navidrome in modo trasparente.

## Stack

- **FastAPI** + **uvicorn**
- **SQLAlchemy** + **Alembic** + **MariaDB**
- **injector** (dependency injection)
- **httpx** (chiamate HTTP async)

## Avvio

```bash
# Con Docker Compose (include MariaDB)
docker compose up -d

# O in locale (serve MariaDB a parte)
uvicorn rivo_drome.api:app --reload --port 8000
```

## Configurazione

Tutte le variabili in `.env`:

| Variabile | Default | Descrizione |
|---|---|---|
| `DB_URL` | `mysql+pymysql://...@mariadb:3306/rivodrome` | Connessione al database |
| `DOWNLOAD_DIR` | `var/music` | Cartella per file scaricati |
| `DOWNLOADER_CHAIN` | `torrent,youtube` | Ordine della catena downloader |
| `JACKETT_URL` | `http://localhost:9117` | URL di Jackett |
| `JACKETT_API_KEY` | — | API key di Jackett |
| `TORRSERVER_URL` | `http://localhost:8090` | URL di TorrServer |
| `NAVIDROME_URL` | `http://localhost:4533` | URL di Navidrome |

## Migrazioni DB

```bash
alembic upgrade head
```

## Comandi CLI

È possibile eseguire comandi da terminale all'interno del container Docker usando `docker compose run --rm`.

### Download Tracce (`track:download`)

Per cercare e scaricare una traccia direttamente dalla CLI (avviando la catena di download):

```bash
docker compose run --rm proxy python -m rivo_drome.cli track:download -q "Queen - Bohemian Rhapsody"
```

