import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";
import { PracticePage } from "./pages/PracticePage";
import { StatsPage } from "./pages/StatsPage";
import { isDevMode } from "./lib/auth";

function NavBar() {
  const devMode = isDevMode();
  return (
    <header className="border-b">
      <div className="max-w-3xl mx-auto px-4 h-14 flex items-center justify-between">
        <span className="font-bold text-primary">DSAT Prep</span>
        <nav className="flex items-center gap-1">
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              `px-3 py-1.5 rounded-md text-sm transition-colors ${
                isActive ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground hover:bg-accent"
              }`
            }
          >
            Practice
          </NavLink>
          <NavLink
            to="/stats"
            className={({ isActive }) =>
              `px-3 py-1.5 rounded-md text-sm transition-colors ${
                isActive ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground hover:bg-accent"
              }`
            }
          >
            Stats
          </NavLink>
        </nav>
        {devMode && (
          <span className="text-xs bg-yellow-100 text-yellow-800 border border-yellow-200 rounded px-2 py-0.5 font-mono">
            DEV USER
          </span>
        )}
      </div>
    </header>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen flex flex-col">
        <NavBar />
        <main className="flex-1 max-w-3xl mx-auto w-full px-4 py-8">
          <Routes>
            <Route path="/" element={<PracticePage />} />
            <Route path="/stats" element={<StatsPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
