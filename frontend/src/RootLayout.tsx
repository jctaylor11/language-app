import { Outlet, Link } from "react-router";

import { useAuth } from "./AuthContext";

export default function RootLayout() {
  const { token, logout } = useAuth();

  return (
    <>
      <nav className="flex justify-end p-5 gap-4 border-b border-gray-300">
        {token != null ? (
          <>
            <Link to="/vocab">Vocab</Link>
            <Link to="/sentences">Sentences</Link>
            <Link to="/dashboard">Dashboard</Link>
            <button onClick={logout} className="cursor-pointer">
              Log out
            </button>
          </>
        ) : (
          <>
            <Link to="/">Home</Link>
            <Link to="/login">Log in</Link>
          </>
        )}
      </nav>
      <main className="px-6 py-8">
        <Outlet />
      </main>
    </>
  );
}
