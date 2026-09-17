import { GlassPane, Reveal3D } from "@/components/depth";

export default function TermsPage() {
  return (
    <main className="legal-page">
      <a href="/">← Back to VAE</a>
      <Reveal3D>
        <p className="legal-kicker">VAE · Terms</p>
        <h1>Use the control room responsibly.</h1>
      </Reveal3D>
      <GlassPane as="section" elevation="floating" className="legal-card">
        <p>
          VAE is a campaign intelligence and workflow tool. You remain responsible for your
          prompts, source material, approvals, publishing decisions, platform policies, and
          generated content.
        </p>
        <h2>Provider access</h2>
        <p>
          Only connect accounts you control. Keep provider permissions minimal and revoke access
          when it is no longer needed.
        </p>
        <h2>Availability</h2>
        <p>
          Staging providers and deterministic generation are provided for evaluation; production
          availability requires an approved deployment plan.
        </p>
      </GlassPane>
      <p className="legal-muted">
        Have counsel review and replace this staging policy before public launch.
      </p>
    </main>
  );
}
