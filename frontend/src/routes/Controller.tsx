import { useEffect } from "react";
import { useNavigate } from "react-router-dom";

import { api } from "../api/client";
import ControllerChat from "../components/controller/ControllerChat";
import { usePageContext } from "../hooks/usePageContext";
import { useWorldStore } from "../stores/world";

export default function Controller() {
  const navigate = useNavigate();
  const context = usePageContext();
  const setProducts = useWorldStore((state) => state.setProducts);
  const setBatches = useWorldStore((state) => state.setBatches);

  useEffect(() => {
    let cancelled = false;
    Promise.all([api.products(), api.batches()])
      .then(([products, batches]) => {
        if (cancelled) return;
        setProducts(products);
        setBatches(batches);
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [setProducts, setBatches]);

  return (
    <div className="min-h-dvh bg-paper">
      <ControllerChat
        variant="page"
        context={context}
        onClose={() => navigate("/")}
      />
    </div>
  );
}
