import { useLocation } from "react-router-dom";

import { usePageContext } from "../../hooks/usePageContext";
import { useControllerStore } from "../../stores/controller";
import ControllerChat from "./ControllerChat";

/** App 级总控浮层：所有页面共用同一个实例与同一段会话。 */
export default function ControllerDock() {
  const { pathname } = useLocation();
  const open = useControllerStore((state) => state.open);
  const setOpen = useControllerStore((state) => state.setOpen);
  const context = usePageContext();

  if (!open) return null;
  if (pathname.startsWith("/controller") || pathname.startsWith("/trace")) return null;

  return <ControllerChat context={context} onClose={() => setOpen(false)} />;
}
