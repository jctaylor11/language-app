import { BrowserRouter, Routes, Route, Navigate } from "react-router";
import VocabSession from "./pages/VocabSession";
import DashboardLayout from "./pages/dashboard/DashboardLayout";
import VocabTable from "./pages/dashboard/VocabTable";
import SentenceSession from "./pages/SentenceSession";
import RootLayout from "./RootLayout";
import DashboardIndex from "./pages/dashboard/DashboardIndex";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<RootLayout />}>
          <Route index element={<Navigate to="/vocab" replace />} />
          <Route path="/vocab" element={<VocabSession />} />
          <Route path="/sentences" element={<SentenceSession />} />
          <Route path="/dashboard" element={<DashboardLayout />}>
            <Route index element={<DashboardIndex />} />
            <Route path="vocabulary" element={<VocabTable />} />
          </Route>
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
