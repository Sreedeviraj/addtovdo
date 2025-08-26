import React, { useEffect, useRef, useState } from "react";

const FixedBoxVideoOverlay = ({ detectedAds, videoElements }) => {
  const videoRefs = useRef({});
  const [activeVideos, setActiveVideos] = useState({});
  const containerRef = useRef(null);

  useEffect(() => {
    // Process newly detected ads
    detectedAds.forEach(ad => {
      const videoId = ad.id;
      const videoEl = videoRefs.current[videoId];
      
      if (!videoEl) return;

      if (ad.status === "new") {
        // New detection - start playing video
        if (!activeVideos[videoId]) {
          videoEl.style.display = "block";
          videoEl.style.position = "absolute";
          videoEl.style.left = `${ad.x}%`;
          videoEl.style.top = `${ad.y}%`;
          videoEl.style.width = `${ad.width}%`;
          videoEl.style.height = `${ad.height}%`;
          videoEl.style.objectFit = "cover";
          videoEl.style.zIndex = "10";
          videoEl.style.borderRadius = "4px";
          videoEl.style.boxShadow = "0 0 10px rgba(0,0,0,0.5)";
          
          // Play the video
          videoEl.currentTime = 0;
          const playPromise = videoEl.play();
          if (playPromise !== undefined) {
            playPromise.catch((e) => console.log("Autoplay prevented:", e));
          }
          
          // Add to active videos
          setActiveVideos(prev => ({
            ...prev,
            [videoId]: {
              element: videoEl,
              position: { x: ad.x, y: ad.y, width: ad.width, height: ad.height },
              startedAt: Date.now(),
              isPlaying: true
            }
          }));
        }
      } else if (ad.status === "active" || ad.status === "tracking") {
        // Update position of active video if it's still playing
        if (activeVideos[videoId] && activeVideos[videoId].isPlaying) {
          videoEl.style.left = `${ad.x}%`;
          videoEl.style.top = `${ad.y}%`;
          videoEl.style.width = `${ad.width}%`;
          videoEl.style.height = `${ad.height}%`;
          
          // Update position in state
          setActiveVideos(prev => ({
            ...prev,
            [videoId]: {
              ...prev[videoId],
              position: { x: ad.x, y: ad.y, width: ad.width, height: ad.height }
            }
          }));
        }
      }
    });
  }, [detectedAds, activeVideos]);

  // Handle video end events
  useEffect(() => {
    const handleVideoEnd = (videoId) => {
      const videoEl = videoRefs.current[videoId];
      if (videoEl) {
        videoEl.style.display = "none";
      }
      setActiveVideos(prev => {
        const newActive = { ...prev };
        delete newActive[videoId];
        return newActive;
      });
    };

    // Add ended event listeners to all videos
    Object.keys(videoRefs.current).forEach(videoId => {
      const videoEl = videoRefs.current[videoId];
      if (videoEl) {
        videoEl.onended = () => handleVideoEnd(videoId);
        // Also handle if video errors
        videoEl.onerror = () => handleVideoEnd(videoId);
      }
    });

    return () => {
      // Clean up event listeners
      Object.keys(videoRefs.current).forEach(videoId => {
        const videoEl = videoRefs.current[videoId];
        if (videoEl) {
          videoEl.onended = null;
          videoEl.onerror = null;
        }
      });
    };
  }, []);

  // Keep videos playing even if they're no longer detected
  // Only remove them when they finish playing
  useEffect(() => {
    const detectedIds = detectedAds.map(ad => ad.id);
    
    // For videos that are no longer detected but still playing,
    // keep them in the active videos state but mark them as not tracking
    Object.keys(activeVideos).forEach(videoId => {
      if (!detectedIds.includes(videoId)) {
        const videoEl = videoRefs.current[videoId];
        if (videoEl && !videoEl.ended) {
          // Video is still playing but marker is no longer detected
          // Keep it playing but don't update its position
          setActiveVideos(prev => ({
            ...prev,
            [videoId]: {
              ...prev[videoId],
              isPlaying: true // Keep it marked as playing
            }
          }));
        }
      }
    });
  }, [detectedAds, activeVideos]);

  return (
    <div ref={containerRef} className="video-overlay-container">
      {Object.values(videoElements).map((video) => (
        <video
          key={video.id}
          ref={(el) => (videoRefs.current[video.id] = el)}
          src={video.src}
          loop={false}
          muted
          playsInline
          preload="auto"
          style={{ display: "none" }}
        />
      ))}
    </div>
  );
};

export default FixedBoxVideoOverlay;