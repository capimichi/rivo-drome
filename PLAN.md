# Piano di Deduplicazione per la Ricerca (Artists e Albums)

## Problema attuale
Nel file `rivo_drome/service/search_service.py`, quando viene effettuata una ricerca verso le API di Deezer (ad esempio tramite l'endpoint `/rest/search3.view`), Deezer restituisce un elenco di **tracce**. 
Per ogni traccia, il codice estrae l'artista e l'album di appartenenza, assicurandosi che esistano a database, e aggiunge gli elementi restituiti alle liste `artists` e `albums` che andranno a formare la risposta `SubsonicResponse`.
Poiché diverse tracce dei risultati appartengono spesso allo stesso artista o allo stesso album, vengono effettuate molteplici `append()` all'interno delle liste, causando dati duplicati nella risposta dell'API Subsonic.

## Soluzione Proposta
Per evitare i duplicati, introdurremo dei `set` per tenere traccia degli ID (di artista e album) già processati durante il ciclo della singola chiamata API. In questo modo inseriremo un determinato artista o album nella risposta Subsonic soltanto la prima volta che lo incontriamo.

### Modifiche richieste in `rivo_drome/service/search_service.py`

1. **Modifica del metodo `search`:**
   Dobbiamo inizializzare i due set di tracciamento e passarli al metodo `_process_deezer_item`.
   
   ```diff
   -    async def search(self, query: str, artist_count: int = 20, album_count: int = 20, song_count: int = 20) -> SearchResult3:
   +    async def search(self, query: str, artist_count: int = 20, album_count: int = 20, song_count: int = 20) -> SearchResult3:
            deezer_data = await self._deezer.search(query, limit=25)
    
            artists = []
            albums = []
            tracks = []
   +        seen_artist_ids = set()
   +        seen_album_ids = set()
    
            for item in deezer_data.get("data", []):
   -            await self._process_deezer_item(item, artists, albums, tracks)
   +            await self._process_deezer_item(item, artists, albums, tracks, seen_artist_ids, seen_album_ids)
   ```

2. **Modifica della firma di `_process_deezer_item`:**
   Aggiungeremo i parametri `seen_artist_ids` e `seen_album_ids` (come `set`).

   ```diff
        async def _process_deezer_item(
            self,
            item: dict,
            artists: List[SubsonicArtist],
            albums: List[SubsonicAlbum],
            tracks: List[SubsonicChild],
   +        seen_artist_ids: set,
   +        seen_album_ids: set,
        ):
   ```

3. **Modifica logica di aggiunta degli artisti:**
   Verificare se l'ID dell'artista è già presente nel set; in caso contrario lo aggiungiamo sia al set che alla lista.

   ```diff
            if deezer_artist.get("id"):
                artist = await self._get_or_create_artist(deezer_artist)
                artist_id = artist.id
   -            artists.append(self._artist_to_subsonic(artist))
   +            if artist_id not in seen_artist_ids:
   +                seen_artist_ids.add(artist_id)
   +                artists.append(self._artist_to_subsonic(artist))
   ```

4. **Modifica logica di aggiunta degli album:**
   Verificare se l'ID dell'album è già presente nel set per l'aggiunta.

   ```diff
            if deezer_album.get("id") and artist_id:
                album = await self._get_or_create_album(deezer_album, artist_id)
   -            albums.append(self._album_to_subsonic(album))
   +            if album.id not in seen_album_ids:
   +                seen_album_ids.add(album.id)
   +                albums.append(self._album_to_subsonic(album))
   ```

## Risultato Atteso
Implementando questa modifica, la risposta Subsonic generata andrà a contenere, per ogni ricerca, un array di `artist` e di `album` univoci, esattamente come si aspetterebbero i client audio, rispettando fedelmente il comportamento nativo di Navidrome o Subsonic.
