# VAE Mobile

The mobile client consumes the versioned VAE API and never contains publishing credentials
or model access. The stabilized Phase 12 contract is:

- `GET /api/v1/workspaces/{workspace_id}/campaigns`
- `GET /api/v1/workspaces/{workspace_id}/media/assets`
- `GET /api/v1/workspaces/{workspace_id}/publishing/accounts`
- `GET /api/v1/workspaces/{workspace_id}/operations/schedule`
- `GET /api/v1/workspaces/{workspace_id}/operations/metrics`
- `GET /api/v1/workspaces/{workspace_id}/operations/audit`

Write actions use the same bearer token and editor permissions as web. A future Flutter shell
should add offline read caching, push notifications for failed jobs, and biometric re-authentication
without duplicating provider logic.
