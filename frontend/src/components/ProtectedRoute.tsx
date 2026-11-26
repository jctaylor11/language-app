import { Outlet, Navigate, useOutletContext } from "react-router";

import type { RootLayoutContext } from "../types";
import { useAuth } from "../AuthContext";

export default function ProtectedRoute() {
  const { isAuthenticated } = useAuth();
  const rootLayoutContext = useOutletContext<RootLayoutContext>(); // Outlet context doesn't reach past this layer unless it is passed on

  if (isAuthenticated === null) {
    return null; // initial value for isAuthenticated is null. isAuthenticated is set in AuthProvider, which is rendered before CheckAuth api is resolved
  }

  if (isAuthenticated) {
    return <Outlet context={rootLayoutContext} />;
  } else {
    return <Navigate to="/login" replace />;
  }
}
