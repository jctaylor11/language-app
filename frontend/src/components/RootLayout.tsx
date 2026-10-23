import { Outlet, Link } from "react-router";

import { useAuth } from "../AuthContext";

export default function RootLayout() {
  const { isAuthenticated, logout } = useAuth();

  return (
    <div className="h-screen flex flex-col">
      <nav className="flex justify-end p-5 gap-4 border-b border-gray-300 shrink-0 text-sm text-[#5B636E] *:hover:text-black">
        {isAuthenticated === true ? (
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
      <main className="flex-1 px-6 py-8">
        <Outlet />
      </main>
    </div>
  );
}
