export default function AccountDeletionPage() {
  return (
    <main className="legal-page">
      <a href="/">← Back to VAE</a>
      <p className="legal-kicker">VAE · Account deletion</p>
      <h1>Request account deletion.</h1>
      <p>
        Signed-in users can request deletion from account settings. The API records the request,
        schedules a 30-day grace period, and gives the workspace owner time to export data or cancel
        an accidental request before the production deletion worker executes it.
      </p>
      <h2>Need help?</h2>
      <p>Contact the workspace administrator and include the account email and workspace name.</p>
      <p className="legal-muted">
        Add a monitored support address and verified legal policy before public launch.
      </p>
    </main>
  );
}
