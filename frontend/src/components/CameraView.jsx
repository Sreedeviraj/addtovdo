import React, { useEffect } from 'react';

const CameraView = ({ onAccessChange, videoRef }) => {
  const enableCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { facingMode: 'environment' } 
      });
      
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      onAccessChange(true);
    } catch (err) {
      console.error('Error accessing camera:', err);
      onAccessChange(false);
    }
  };

  // Cleanup when unmounting
  useEffect(() => {
    return () => {
      if (videoRef.current && videoRef.current.srcObject) {
        const tracks = videoRef.current.srcObject.getTracks();
        tracks.forEach(track => track.stop());
      }
    };
  }, [videoRef]);

  return (
    <div className="camera-section">
      <button onClick={enableCamera} className="start-camera-btn">
        📷 Start Camera
      </button>
      <video 
        ref={videoRef}
        autoPlay 
        playsInline 
        muted 
        className="camera-feed"
      />
    </div>
  );
};

export default CameraView;



