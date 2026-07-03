import { Outlet, Link } from "react-router";

export default function RootLayout() {
  return (
    <>
      <nav className="flex justify-end p-5 gap-4 border-b border-gray-300">
        <Link to="/vocab">Vocab</Link>
        <Link to="/sentences">Sentences</Link>
        <Link to="/dashboard">Dashboard</Link>
        <Link to="/login">Log in</Link>
      </nav>
      <main className="px-6 py-8">
        <Outlet />
      </main>
    </>
  );
}
