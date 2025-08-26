import React, { useEffect } from "react";

const AdDetector = ({ videoRef, canvasRef, onAdDetected }) => {
  useEffect(() => {
    let ws = null;
    let animationFrameId = null;
    let reconnectTimeout = null;
    let isConnected = false;
    let frameInterval = 150; // Process every 150ms (~6.5fps) for faster response

    const initWS = () => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        return;
      }

      try {
        ws = new WebSocket("ws://localhost:8000/ws/detect");

        ws.onopen = () => {
          console.log("✅ Connected to backend");
          isConnected = true;
          let lastFrameTime = 0;
          
          // Start sending frames
          const sendFrame = (timestamp) => {
            if (!isConnected) return;
            
            const video = videoRef.current;
            const canvas = canvasRef.current;

            if (video && video.readyState === 4 && canvas && isConnected) {
              // Throttle frame rate
              if (timestamp - lastFrameTime > frameInterval) {
                lastFrameTime = timestamp;
                
                const ctx = canvas.getContext("2d");
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;

                ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                
                // Convert to JPEG and send as base64
                canvas.toBlob(
                  (blob) => {
                    if (blob && ws && ws.readyState === WebSocket.OPEN) {
                      const reader = new FileReader();
                      reader.onloadend = () => {
                        // Strip header like "data:image/jpeg;base64,"
                        const base64data = reader.result.split(",")[1];
                        ws.send(base64data);
                      };
                      reader.readAsDataURL(blob);
                    }
                  },
                  "image/jpeg",
                  0.7 // Medium quality for faster transmission
                );
              }
            }

            animationFrameId = requestAnimationFrame(sendFrame);
          };

          animationFrameId = requestAnimationFrame(sendFrame);
        };

        ws.onmessage = (event) => {
          try {
            const detectedAds = JSON.parse(event.data);
            onAdDetected(detectedAds);
          } catch (err) {
            console.error("❌ Failed to parse WS message:", err);
          }
        };

        ws.onclose = () => {
          console.log("❌ WS closed, retrying in 2s...");
          isConnected = false;
          if (animationFrameId) {
            cancelAnimationFrame(animationFrameId);
          }
          // Auto-reconnect with backoff
          reconnectTimeout = setTimeout(initWS, 2000);
        };

        ws.onerror = (error) => {
          console.error("WebSocket error:", error);
          isConnected = false;
        };
      } catch (error) {
        console.error("Failed to create WebSocket:", error);
        reconnectTimeout = setTimeout(initWS, 2000);
      }
    };

    initWS();

    // Cleanup on unmount
    return () => {
      isConnected = false;
      if (animationFrameId) {
        cancelAnimationFrame(animationFrameId);
      }
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
      }
      if (ws) {
        ws.close();
      }
    };
  }, [videoRef, canvasRef, onAdDetected]);

  return (
    <canvas
      ref={canvasRef}
      style={{ display: "none" }} // hidden canvas, used for frame capture
    />
  );
};

export default AdDetector;