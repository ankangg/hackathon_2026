import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Polaris AI — Antarctic Navigation Console",
  description: "Tactical maritime decision-support console for Weddell Sea ice and iceberg navigation (SIH26059 / NCPOR)",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <head>
        <link
          rel="stylesheet"
          href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
          integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="
          crossOrigin=""
        />
      </head>
      <body className="bg-background text-white min-h-screen antialiased selection:bg-accent selection:text-black">
        {children}
      </body>
    </html>
  );
}
