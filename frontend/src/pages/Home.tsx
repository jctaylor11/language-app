import { Navigate } from "react-router";
import { useAuth } from "../AuthContext";

export default function Home() {
  const { token } = useAuth();

  if (token) {
    return <Navigate to="/vocab" replace />;
  }

  return "Placeholder for landing page";
}
