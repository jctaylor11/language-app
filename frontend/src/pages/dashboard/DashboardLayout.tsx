import { Outlet, Link } from "react-router";

const links = [
  { to: "/dashboard", label: "Overview" },
  { to: "/dashboard/vocabulary", label: "Vocab Vault" },
  { to: "/dashboard/sentences", label: "Sentence Vault" },
];

export default function DashboardLayout() {
  return (
    <div className="flex gap-10">
      <aside className="w-35 shrink-0">
        <nav className="flex flex-col gap-2">
          {links.map(({ to, label }) => (
            <Link key={to} to={to}>
              {label}
            </Link>
          ))}
        </nav>
      </aside>
      <main className="flex-1 min-w-0">
        <Outlet />
      </main>
    </div>
  );
}
