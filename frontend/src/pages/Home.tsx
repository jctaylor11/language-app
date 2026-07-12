import { Navigate } from "react-router";
import { useAuth } from "../AuthContext";

export default function Home() {
  const { isAuthenticated } = useAuth();

  if (isAuthenticated === null) {
    return null; // Otherwise there will be a flash of the page before isAuthenticated resolves in the AuthProvider's checkAuthStatus useEffect. Its resolution updates auth state which triggers the rerender
  }

  if (isAuthenticated) {
    return <Navigate to="/vocab" replace />;
  }

  return "Placeholder for landing page";
}
