import React from 'react';

const DebugInfo = ({ detectedAds }) => {
  if (detectedAds.length === 0) return null;
  
  return (
    <div style={{
      position: 'fixed',
      bottom: '10px',
      left: '10px',
      background: 'rgba(0,0,0,0.7)',
      color: 'white',
      padding: '10px',
      borderRadius: '5px',
      zIndex: 1000,
      fontSize: '12px',
      maxWidth: '300px'
    }}>
      <h4>Detected Ads (Debug):</h4>
      {detectedAds.map(ad => (
        <div key={ad.id} style={{marginBottom: '5px'}}>
          <div>ID: {ad.id}</div>
          <div>Name: {ad.name}</div>
          <div>Score: {(ad.score * 100).toFixed(1)}%</div>
        </div>
      ))}
    </div>
  );
};

export default DebugInfo;