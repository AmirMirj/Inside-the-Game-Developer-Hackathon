import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "Inside the Game — Studio Console",
  description:
    "Synthetic match insights studio console: live events, state, and timed overlays.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
