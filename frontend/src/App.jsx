import React, { useState, useRef, useEffect } from "react";
import CameraView from "./components/CameraView";
import AdDetector from "./components/AdDetector";
import FixedBoxVideoOverlay from "./components/FixedBoxVideoOverlay";
import AdminPanel from "./components/AdminPanel";
import { BACKEND_URL } from "./config";
import "./App.css";

function App() {
  const [hasCameraAccess, setHasCameraAccess] = useState(false);
  const [detectedAds, setDetectedAds] = useState([]);
  const [videoElements, setVideoElements] = useState({});
  const [showAdmin, setShowAdmin] = useState(false);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);

  // Fetch ad mappings and videos from backend
  useEffect(() => {
    const fetchMappings = async () => {
      try {
        const response = await fetch(`${BACKEND_URL}/api/ads`);
        const mappings = await response.json();
        const videoMap = {};
        for (const mapping of mappings) {
          videoMap[mapping._id] = {
            id: mapping._id,
            src: `${BACKEND_URL}${mapping.videoUrl}`,
            name: mapping.name
          };
        }
        setVideoElements(videoMap);
      } catch (error) {
        console.error("Failed to fetch ad mappings:", error);
      }
    };
    fetchMappings();
  }, []);

  return (
    <div className="App">
      <header className="app-header">
        <h1 className="brand-title">🎥 Ad-to-Video</h1>
        <button className="admin-toggle" onClick={() => setShowAdmin(!showAdmin)}>
          {showAdmin ? "⬅ Back to Camera" : "⚙ Admin Panel"}
        </button>
      </header>

      {showAdmin ? (
        <AdminPanel />
      ) : (
        <>
          <div className="camera-wrapper">
            <div className="camera-container">
              <CameraView onAccessChange={setHasCameraAccess} videoRef={videoRef} />
              {hasCameraAccess && (
                <AdDetector
                  videoRef={videoRef}
                  canvasRef={canvasRef}
                  onAdDetected={setDetectedAds}
                />
              )}

              {/* Video overlay that plays within the detected rectangle */}
              <FixedBoxVideoOverlay
                detectedAds={detectedAds}
                videoElements={videoElements}
              />
            </div>
          </div>

          <div className={`status-bar ${hasCameraAccess ? "active" : "inactive"}`}>
            {hasCameraAccess ? (
              <span>✅ Camera Active - Point at a registered marker</span>
            ) : (
              <span>🚫 Waiting for Camera Access...</span>
            )}
          </div>
        </>
      )}
    </div>
  );
}

export default App;