import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { LandingPage } from "./pages/LandingPage";
import { TranslationPage } from "./pages/TranslationPage";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/translate" element={<TranslationPage />} />
        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;