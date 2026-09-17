# AIStor Free local setup

AIStor Free is licensed for community use and supports a single-node deployment. The license is
not an `AEVRA_TOKEN_VAULT_KEY` and must never be committed to this repository.

## Start it

1. Create `infrastructure/secrets/minio.license` and paste the license value exactly as downloaded
   from MinIO SUBNET. The directory is ignored by Git.
2. Put strong values in `.env`:

   ```text
   MINIO_ACCESS_KEY=aevraadmin
   MINIO_SECRET_KEY=<long-random-admin-password>
   ```

   These values are mapped to `MINIO_ROOT_USER` and `MINIO_ROOT_PASSWORD` by Compose. The
   `AEVRA_MINIO_ACCESS_KEY`/`AEVRA_MINIO_SECRET_KEY` aliases are also accepted, so the values used
   by the API and console stay in sync. They are read only when the persistent `aistor_data` volume
   is initialized; changing `.env` later does not rename an existing root user.

   If the console says the access key does not exist, first inspect the credentials actually passed
   to the running container:

   ```powershell
   docker compose --profile aistor exec aistor sh -lc 'printf "root user: %s\n" "$MINIO_ROOT_USER"'
   ```

   A pre-existing volume may still contain older credentials. If it contains no data you need, reset
   only that AIStor volume (this permanently deletes objects in it):

   ```powershell
   docker compose --profile aistor down
   docker volume ls --format '{{.Name}}' | Select-String 'aistor_data'
   # Copy the exact volume name printed above, then remove only that volume:
   docker volume rm <exact-aistor-volume-name>
   docker compose --profile aistor up -d aistor
   ```

   If the volume contains data, do not remove it—log in with the original root username/password or
   recover the objects before rotating credentials.

3. Start the optional profile:

   ```powershell
   docker compose --profile aistor up -d aistor
   docker compose logs -f aistor
   ```

4. Open the AIStor Console at `http://localhost:9101`. Its S3 API is at
   `http://localhost:9100`.
5. Create a private `aevra-assets` bucket and an application access key in the Console.

For the API container, configure:

```text
AEVRA_STORAGE_BACKEND=s3
AEVRA_MINIO_ENDPOINT=aistor:9000
AEVRA_MINIO_ACCESS_KEY=<application-access-key>
AEVRA_MINIO_SECRET_KEY=<application-secret-key>
AEVRA_MINIO_BUCKET=aevra-assets
AEVRA_MINIO_SECURE=false
```

`AEVRA_MINIO_ENDPOINT` is the S3 API host, not the AIStor web console. Use `aistor:9000` when
the API runs in this Compose stack. For a Render-deployed API, `aistor:9000`, `localhost`, and
`127.0.0.1` are unreachable; expose the S3 API through a public TLS hostname and enter only the
hostname (no `https://`, path, or trailing slash), for example:

```text
AEVRA_MINIO_ENDPOINT=storage.example.com
AEVRA_MINIO_SECURE=true
```

The hostname must resolve to the AIStor S3 API (port 9000 behind TLS/443), not the console (port
9001). A temporary tunnel hostname such as `abc123.ngrok-free.app` also works for testing, but it
changes or stops when the tunnel closes and should not be used for production persistence.

Then start the API and web services with the same profile:

```powershell
docker compose --profile aistor up -d --build api web
```

For Render, `aistor:9000` and `localhost:9100` will not work: Render needs a reachable HTTPS
AIStor/S3 endpoint. Set `AEVRA_MINIO_SECURE=true` and use the public endpoint only after TLS,
firewall rules, and backups are configured.
