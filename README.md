# Jellyfin Backup Utilities

Small helpers to back up or copy Jellyfin state between databases:

- `backup-restore.py` – Export/import played + favourites via Jellyfin API.
- `copy-dates.py` – Copy `DateCreated`/`DateModified`/`DateLastMediaAdded` between SQLite DBs (match by `Name`/`Type`/`Path`).
- `copy-userdata.py` – Copy watch history/favourites between SQLite DBs (match users by username, items by `Name`/`Path`/`Type`).

## Direct usage

Environment: set `JELLYFIN_URL` (base URL with scheme, e.g. `http://localhost:8096`) and `JELLYFIN_API_KEY` (admin key). You can put them in a `.env` file; they’re read via `python-dotenv`.

```bash
# Backup (needs username)
python backup-restore.py --username alice --backup
# Backup all users
python backup-restore.py --backup

# Restore from jellyfin.json (username comes from the file; no CLI username needed)
python backup-restore.py --restore
python backup-restore.py --restore --dryrun  # simulate restore

How it works:
- `backup-restore.py` calls the Jellyfin API with your key to list items for the given user (or all users), writes selections to `jellyfin.json`, and on restore uses API calls to mark favorites/played based on that file.

python copy-dates.py --source-db /path/to/source.db --dest-db /var/lib/jellyfin/data/jellyfin.db
python copy-userdata.py --source-db /path/to/source.db --dest-db /var/lib/jellyfin/data/jellyfin.db
```

Notes:
- `--source-db` is required for the copy scripts.
- `--dest-db` defaults to `/var/lib/jellyfin/data/jellyfin.db`.

## Nix (flake) usage

```bash
nix run .#copy-dates -- --source-db /path/to/source.db
nix run .#copy-userdata -- --source-db /path/to/source.db
nix run .#backup-restore -- --username alice --backup
nix run .#backup-restore -- --backup   # all users
nix run .#backup-restore -- --restore
nix run .#backup-restore -- --restore --dryrun
nix develop   # drop into a shell with dependencies

# Pass env vars inline when running with nix
JELLYFIN_URL=http://localhost:8096 JELLYFIN_API_KEY=abcd \
  nix run .#backup-restore -- --backup --username alice
```

The flake pins `nixpkgs` to `nixos-25.11` and builds Python with `requests` and `python-dotenv`. Apps are exposed for each script so you can run them from any machine with Nix.

Environment with Nix:
- Inline as above; or
- Put `JELLYFIN_URL`/`JELLYFIN_API_KEY` in a `.env` in the directory you run from; `python-dotenv` loads it (searches current dir and parents) even when invoked via `nix run`.
