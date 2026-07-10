import { BrowserRouter, Routes, Route, Navigate } from "react-router";
import VocabSession from "./pages/VocabSession";
import DashboardLayout from "./pages/dashboard/DashboardLayout";
import VocabTable from "./pages/dashboard/VocabTable";
import SentenceSession from "./pages/SentenceSession";
import RootLayout from "./RootLayout";
import DashboardIndex from "./pages/dashboard/DashboardIndex";
import Login from "./pages/login";
import { GoogleOAuthProvider } from "@react-oauth/google";
import { AuthProvider } from "./AuthContext";
import ProtectedRoute from "./ProtectedRoute";

export default function App() {
  return (
    <BrowserRouter>
      <GoogleOAuthProvider
        clientId={import.meta.env.VITE_OIDC_GOOGLE_CLIENT_ID}
      >
        <AuthProvider>
          <Routes>
            <Route element={<RootLayout />}>
              <Route element={<ProtectedRoute />}>
                <Route index element={<Navigate to="/vocab" replace />} />
                <Route path="/vocab" element={<VocabSession />} />
                <Route path="/sentences" element={<SentenceSession />} />
                <Route path="/dashboard" element={<DashboardLayout />}>
                  <Route index element={<DashboardIndex />} />
                  <Route path="vocabulary" element={<VocabTable />} />
                </Route>
              </Route>
              <Route path="/login" element={<Login />} />
            </Route>
          </Routes>
        </AuthProvider>
      </GoogleOAuthProvider>
    </BrowserRouter>
  );
}
