# OAuth integration policy

Each network is implemented behind a `SocialPublisher` adapter. OAuth callbacks terminate at the API, validate signed state, bind the result to the initiating workspace, and store encrypted credentials. Refresh and publish operations run in the publishing service. Browser code and agents see only capability metadata such as account identity, granted scopes, and connection health.

Platform-specific scopes, review requirements, and deletion/webhook rules will be documented beside each adapter when that connector phase begins.

