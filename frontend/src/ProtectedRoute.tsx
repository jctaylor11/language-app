import { Outlet, Navigate } from "react-router";

import { useAuth } from "./AuthContext";

export default function ProtectedRoute() {
  const { token } = useAuth();

  if (token !== null) {
    return <Outlet />;
  } else {
    return <Navigate to="/login" replace />;
  }
}
