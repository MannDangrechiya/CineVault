// CineVault OS — Next.js App Router Not Found Page
// Handles 404 errors globally across the application.

import Link from "next/link";

export default function NotFound() {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        minHeight: "100vh",
        background: "#0a0a0a",
        color: "#e0e0e0",
        fontFamily: "'Inter', 'Segoe UI', sans-serif",
        padding: "2rem",
        textAlign: "center",
      }}
    >
      <h1
        style={{
          fontSize: "6rem",
          fontWeight: 800,
          background: "linear-gradient(135deg, #ff6b35, #ff3366)",
          WebkitBackgroundClip: "text",
          WebkitTextFillColor: "transparent",
          margin: 0,
          lineHeight: 1,
        }}
      >
        404
      </h1>
      <p
        style={{
          fontSize: "1.25rem",
          color: "#888",
          margin: "1rem 0 2rem",
          maxWidth: "400px",
        }}
      >
        This page doesn&apos;t exist in the vault. It may have been moved or
        removed.
      </p>
      <Link
        href="/dashboard"
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: "0.5rem",
          padding: "0.75rem 1.5rem",
          borderRadius: "8px",
          background: "linear-gradient(135deg, #ff6b35, #ff3366)",
          color: "#fff",
          fontWeight: 600,
          fontSize: "0.95rem",
          textDecoration: "none",
          transition: "opacity 0.2s",
        }}
      >
        ← Back to Dashboard
      </Link>
    </div>
  );
}
