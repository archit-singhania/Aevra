import type { Metadata, Viewport } from "next";
import { DepthField } from "../components/depth-field";
import "./globals.css";

export const metadata: Metadata = {
  title: "VAE — Campaign Intelligence",
  description: "Plan, generate, approve, and orchestrate brand-grounded campaigns.",
  icons: { icon: "/favicon.svg" },
};

// Kept in sync with --bg in globals.css. It was still the pre-rebrand
// #07090d, so the browser chrome on mobile didn't match the app.
export const viewport: Viewport = { themeColor: "#0a0b0d", colorScheme: "dark" };

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        {children}
        {/* One delegated pointer listener drives tilt for every surface in
            the app — see components/depth-field.tsx for why it lives here
            rather than in each card. */}
        <DepthField />
      </body>
    </html>
  );
}
