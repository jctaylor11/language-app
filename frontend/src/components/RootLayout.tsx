import { useState } from "react";
import { Outlet, Link, NavLink } from "react-router";

import { useAuth } from "../AuthContext";

const navItemClassName =
  "flex items-center h-9 px-3 rounded-md text-body transition-colors duration-120 outline-none focus-visible:shadow-focus";

function getNavItemClassName({ isActive }: { isActive: boolean }): string {
  if (isActive) {
    return `${navItemClassName} bg-surface-muted text-ink`;
  }
  return `${navItemClassName} text-ink-muted hover:bg-surface-muted hover:text-ink`;
}

export default function RootLayout() {
  const { isAuthenticated, logout } = useAuth();
  const [focusMode, setFocusMode] = useState(false); // Set by pages (e.g. a running session) that need the full screen

  let mainClassName = "flex-1 px-6 py-8";
  if (focusMode) {
    mainClassName = "flex-1"; // The page's own header spans the full width
  }

  return (
    <div className="h-screen flex flex-col">
      {focusMode === false && (
        <nav className="flex items-center justify-between h-16 px-8 border-b border-line shrink-0">
          <Link
            to="/"
            className="text-subheading font-semibold text-ink rounded-md outline-none focus-visible:shadow-focus"
          >
            Sanggi
          </Link>
          <div className="flex items-center gap-1">
            {isAuthenticated === true ? (
              <>
                <NavLink to="/vocab" className={getNavItemClassName}>
                  Vocab
                </NavLink>
                <NavLink to="/sentences" className={getNavItemClassName}>
                  Sentences
                </NavLink>
                <NavLink to="/dashboard" className={getNavItemClassName}>
                  Dashboard
                </NavLink>
                <button
                  onClick={logout}
                  className={`${navItemClassName} text-ink-muted hover:bg-surface-muted hover:text-ink cursor-pointer`}
                >
                  Log out
                </button>
              </>
            ) : (
              <>
                <NavLink to="/" end className={getNavItemClassName}>
                  Home
                </NavLink>
                <NavLink to="/login" className={getNavItemClassName}>
                  Log in
                </NavLink>
              </>
            )}
          </div>
        </nav>
      )}
      <main className={mainClassName}>
        <Outlet context={{ setFocusMode }} />
      </main>
    </div>
  );
}
