import { createRoot } from "react-dom/client";
import App from "./App";
import "./index.css";
import { Toaster } from "@/components/ui/toaster";
import { useEffect } from "react";
import { apiRequest } from "./lib/queryClient";

// Initialize demo data for development only
function DemoDataInitializer() {
  useEffect(() => {
    const initDemoData = async () => {
      try {
        await apiRequest("POST", "/api/init-demo-data", {});
        console.log("Demo data initialized successfully");
      } catch (error) {
        console.error("Failed to initialize demo data:", error);
      }
    };

    initDemoData();
  }, []);

  return null;
}

createRoot(document.getElementById("root")!).render(
  <>
    <App />
    <Toaster />
    <DemoDataInitializer />
  </>
);
