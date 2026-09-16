import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "IT Support Portal",
  description: "IT Support Ticketing Dashboard",
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