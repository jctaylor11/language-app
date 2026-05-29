import { BrowserRouter, Routes, Route } from "react-router";
import VocabSession from "./pages/VocabSession";
import Dashboard from "./pages/Dashboard";
import SentenceSession from "./pages/SentenceSession";
import Layout from "./Layout";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<VocabSession />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/sentences" element={<SentenceSession />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
