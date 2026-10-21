import { Route, Routes } from "react-router-dom";

import Sandbox from "./routes/Sandbox";
import Trace from "./routes/Trace";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Sandbox />} />
      <Route path="/trace/:code" element={<Trace />} />
    </Routes>
  );
}
