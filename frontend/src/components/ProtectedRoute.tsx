import { Outlet, Navigate } from "react-router";

import { useAuth } from "../AuthContext";

export default function ProtectedRoute() {
  const { isAuthenticated } = useAuth();

  if (isAuthenticated === null) {
    return null; // initial value for isAuthenticated is null. isAuthenticated is set in AuthProvider, which is rendered before CheckAuth api is resolved
  }

  if (isAuthenticated) {
    return <Outlet />;
  } else {
    return <Navigate to="/login" replace />;
  }
}
