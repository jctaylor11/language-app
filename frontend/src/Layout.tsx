import { Outlet, Link } from "react-router";

export default function Layout() {
  return (
    <>
      <nav className="flex justify-end p-5 gap-4">
        <Link to="/sentences">Sentences</Link>
        <Link to="/dashboard">Dashboard</Link>
      </nav>
      <Outlet />
    </>
  );
}
