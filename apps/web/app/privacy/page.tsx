export default function PrivacyPage() {
  return (
    <main className="legal-page">
      <a href="/">← Back to VAE</a>
      <p className="legal-kicker">VAE · Privacy</p>
      <h1>Privacy, with a clear paper trail.</h1>
      <p>
        VAE stores workspace content, campaign decisions, and operational events so teams can create
        and review grounded campaigns. Provider credentials are encrypted at rest and are never
        returned by the API.
      </p>
      <h2>What we collect</h2>
      <p>
        Account identity, workspace data, uploaded knowledge, generated assets, and audit events.
      </p>
      <h2>Your controls</h2>
      <p>
        You can export workspace data, disconnect providers, and request account deletion from the
        account controls.
      </p>
      <p className="legal-muted">
        Replace this staging policy with reviewed jurisdiction-specific language before public
        launch.
      </p>
    </main>
  );
}
