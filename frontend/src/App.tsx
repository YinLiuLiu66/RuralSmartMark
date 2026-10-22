import { lazy, Suspense } from "react";
import { Route, Routes } from "react-router-dom";

const Sandbox = lazy(() => import("./routes/Sandbox"));
const Trace = lazy(() => import("./routes/Trace"));

function PageFallback() {
  return (
    <div className="flex min-h-dvh items-center justify-center bg-paper">
      <div className="text-center">
        <div className="font-display text-2xl text-ink">智农云链</div>
        <div className="mx-auto mt-4 h-1.5 w-28 overflow-hidden rounded-full bg-line">
          <div className="h-full w-1/2 animate-pulse rounded-full bg-apple" />
        </div>
        <p className="mt-3 text-xs text-ink-muted">正在打开页面…</p>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <Suspense fallback={<PageFallback />}>
      <Routes>
        <Route path="/" element={<Sandbox />} />
        <Route path="/trace/:code" element={<Trace />} />
      </Routes>
    </Suspense>
  );
}
