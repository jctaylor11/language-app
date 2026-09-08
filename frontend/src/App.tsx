import { BrowserRouter, Routes, Route } from "react-router";
import VocabSession from "./pages/VocabSession";
import DashboardLayout from "./pages/dashboard/DashboardLayout";
import VocabVault from "./pages/dashboard/VocabVault";
import SentenceSession from "./pages/SentenceSession";
import SessionLog from "./pages/dashboard/SessionLog";
import RootLayout from "./RootLayout";
import DashboardIndex from "./pages/dashboard/DashboardIndex";
import Login from "./pages/Login";
import Home from "./pages/Home";
import { GoogleOAuthProvider } from "@react-oauth/google";
import { AuthProvider } from "./AuthContext";
import ProtectedRoute from "./ProtectedRoute";
import SentenceVault from "./pages/dashboard/SentenceVault";

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
                <Route path="/vocab" element={<VocabSession />} />
                <Route path="/sentences" element={<SentenceSession />} />
                <Route path="/dashboard" element={<DashboardLayout />}>
                  <Route index element={<DashboardIndex />} />
                  <Route path="vocabulary" element={<VocabVault />} />
                  <Route path="sentences" element={<SentenceVault />} />
                  <Route path="session-log" element={<SessionLog />} />
                  <Route
                    path="session-log/:sessionNumber"
                    element={<SessionLog />}
                  />
                </Route>
              </Route>
              <Route path="/" element={<Home />} />
              <Route path="/login" element={<Login />} />
            </Route>
          </Routes>
        </AuthProvider>
      </GoogleOAuthProvider>
    </BrowserRouter>
  );
}
