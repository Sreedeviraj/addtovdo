import React, { useEffect, useRef, useState } from "react";

const FixedBoxVideoOverlay = ({ detectedAds, videoElements }) => {
  const videoRefs = useRef({});
  const [playedVideos, setPlayedVideos] = useState({}); // Track videos that already played

  useEffect(() => {
    detectedAds.forEach((ad) => {
      const videoId = ad.id;

      // If this video already played, skip it
      if (playedVideos[videoId]) return;

      const videoEl = videoRefs.current[videoId];
      if (!videoEl) return;

      // Show and play the video
      videoEl.style.display = "block";
      videoEl.style.position = "absolute";
      videoEl.style.left = "50%";
      videoEl.style.top = "50%";
      videoEl.style.transform = "translate(-50%, -50%)"; // center
      videoEl.style.width = "400px"; // fixed size box
      videoEl.style.height = "300px";
      videoEl.style.objectFit = "cover";
      videoEl.style.zIndex = "10";

      const playPromise = videoEl.play();
      if (playPromise !== undefined) {
        playPromise.catch((e) => console.log("Autoplay prevented:", e));
      }

      // Mark as played when ended
      const handleEnded = () => {
        videoEl.style.display = "none";
        setPlayedVideos((prev) => ({ ...prev, [videoId]: true }));
        videoEl.removeEventListener("ended", handleEnded);
      };
      videoEl.addEventListener("ended", handleEnded);
    });
  }, [detectedAds, playedVideos]);

  return (
    <div className="fixed-box-video-overlay">
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
