import { BrowserRouter, Routes, Route } from "react-router-dom";

import { PaperProvider } from "./context/PaperContext";

import AuthPage from "./pages/AuthPage";
import ProtectedRoute from "./components/ProtectedRoute";

import Research from "./pages/Research";
import Papers from "./pages/Papers";
import Compare from "./pages/Compare";
import Library from "./pages/Library";
import PaperReader from "./pages/PaperReader";


function App() {
  return (
    <BrowserRouter>
      <PaperProvider>
        <Routes>
          <Route path="/auth" element={<AuthPage />} />

          <Route path="/" element={<ProtectedRoute><Research /></ProtectedRoute>} />
          <Route path="/papers" element={<ProtectedRoute><Papers /></ProtectedRoute>} />
          <Route path="/compare" element={<ProtectedRoute><Compare /></ProtectedRoute>} />
          <Route path="/library" element={<ProtectedRoute><Library /></ProtectedRoute>} />
          <Route path="/paper/:id" element={<ProtectedRoute><PaperReader /></ProtectedRoute>} />
        </Routes>
      </PaperProvider>
    </BrowserRouter>
  );
}

export default App;