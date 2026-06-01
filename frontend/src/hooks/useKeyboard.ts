import { useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useUIStore } from "@/stores/uiStore";

export function useKeyboard() {
  const navigate = useNavigate();
  const { openModal, closeModal, activeModal } = useUIStore();

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "k") {
        e.preventDefault();
        openModal("search");
        return;
      }
      if (e.key === "Escape" && activeModal) {
        e.preventDefault();
        closeModal();
        return;
      }
      if (e.key === "/" && !activeModal && !(e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement)) {
        e.preventDefault();
        navigate("/chat");
        return;
      }
    },
    [navigate, openModal, closeModal, activeModal]
  );

  useEffect(() => {
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [handleKeyDown]);
}
