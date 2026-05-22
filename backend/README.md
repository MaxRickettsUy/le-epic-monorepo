# HC Archives Back

## Seed Bands
1. `docker compose up --build`
2. `docker exec -it hc_archive_back /bin/sh`
3. `python seed_bands.py`

## Using Blocklist
see /data/block_list.json
1. `docker compose up --build`
2. `docker exec -it hc_archives_back /bin/sh`
3. `python seed_bands_with_blocklist.py`
4. `python generate_blocklist_from_releases.py` -> this will append new bands to /data/block_list.json on your local disk
