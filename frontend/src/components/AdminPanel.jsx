import React, { useState, useEffect } from "react";

const BACKEND_URL = "http://127.0.0.1:8000";

const AdminPanel = () => {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [imageFile, setImageFile] = useState(null);
  const [videoFile, setVideoFile] = useState(null);
  const [ads, setAds] = useState([]);
  const [editingAd, setEditingAd] = useState(null);
  const [editName, setEditName] = useState("");
  const [editDescription, setEditDescription] = useState("");

  // Fetch ads
  const fetchAds = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/ads`);
      const data = await res.json();
      setAds(data);
    } catch (err) {
      console.error("Error fetching ads:", err);
    }
  };

  useEffect(() => {
    fetchAds();
  }, []);

  // Submit new ad
  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!name || !imageFile || !videoFile) {
      alert("Please provide name, image, and video!");
      return;
    }

    const formData = new FormData();
    formData.append("name", name);
    formData.append("description", description);
    formData.append("image", imageFile);
    formData.append("video", videoFile);

    try {
      const res = await fetch(`${BACKEND_URL}/api/ads`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) throw new Error("Failed to create ad");

      const data = await res.json();
      console.log("Uploaded:", data);

      // Clear form
      setName("");
      setDescription("");
      setImageFile(null);
      setVideoFile(null);
      if (document.querySelector('input[type="file"]')) {
        document.querySelector('input[type="file"]').value = "";
      }

      // Refresh list
      fetchAds();
    } catch (err) {
      console.error("Error uploading:", err);
      alert("Error uploading ad. Please try again.");
    }
  };

  // Delete ad
  const handleDelete = async (adId) => {
    if (!window.confirm("Are you sure you want to delete this ad?")) return;

    try {
      const res = await fetch(`${BACKEND_URL}/api/ads/${adId}`, {
        method: "DELETE",
      });

      if (!res.ok) throw new Error("Failed to delete ad");

      // Refresh list
      fetchAds();
    } catch (err) {
      console.error("Error deleting ad:", err);
      alert("Error deleting ad. Please try again.");
    }
  };

  // Start editing an ad
  const startEdit = (ad) => {
    setEditingAd(ad);
    setEditName(ad.name);
    setEditDescription(ad.description || "");
  };

  // Cancel editing
  const cancelEdit = () => {
    setEditingAd(null);
    setEditName("");
    setEditDescription("");
  };

  // Save edited ad
  const saveEdit = async () => {
    if (!editName.trim()) {
      alert("Name cannot be empty!");
      return;
    }

    try {
      const res = await fetch(`${BACKEND_URL}/api/ads/${editingAd._id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name: editName,
          description: editDescription,
        }),
      });

      if (!res.ok) throw new Error("Failed to update ad");

      // Refresh list
      fetchAds();
      cancelEdit();
    } catch (err) {
      console.error("Error updating ad:", err);
      alert("Error updating ad. Please try again.");
    }
  };

  return (
    <div style={{ padding: "20px" }}>
      <h2>Create New Ad</h2>
      <form onSubmit={handleSubmit} style={{ marginBottom: "30px" }}>
        <div style={{ marginBottom: "10px" }}>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Ad Name"
            required
           className="p-8 w-[300px] border border-gray-300 rounded h-10  "
          />
        </div>
        <div style={{ marginBottom: "10px" }}>
          <input
            type="text"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Description (optional)"
           className="p-8 w-[300px] border border-gray-300 rounded h-10 "
            
          />
        </div>
        <div style={{ marginBottom: "10px" }}>
          <label>Marker Image: </label>
          <input
            type="file"
            accept="image/*"
            onChange={(e) => setImageFile(e.target.files[0])}
            required
          />
        </div>
        <div style={{ marginBottom: "10px" }}>
          <label>Video File: </label>
          <input
            type="file"
            accept="video/*"
            onChange={(e) => setVideoFile(e.target.files[0])}
            required
          />
        </div>
        <button type="submit" className="h-10 w-30  bg-violet-600 text-white py-3 px-8 rounded-2xl font-medium hover:bg-violet-700 transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2">
          Upload Ad
        </button>
      </form>

      <h2 className="text-xl font-bold text-gray-900">All Ads</h2>
<div className="flex flex-wrap gap-5 p-4 mt-20">
  {ads.map((ad) => (
    <div 
      key={ad._id} 
      className="border border-gray-300 p-4 w-[300px] relative rounded-xl shadow-sm" // REMOVED mt-10
    >
  {editingAd && editingAd._id === ad._id ? (
    <div>
      <input
        type="text"
        value={editName}
        onChange={(e) => setEditName(e.target.value)}
        className="mb-3 p-2 w-full border border-gray-300 rounded-md focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
      />
      <input
        type="text"
        value={editDescription}
        onChange={(e) => setEditDescription(e.target.value)}
        className="mb-3 p-2 w-full border border-gray-300 rounded-md focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
        placeholder="Description (optional)"
      />
      <div className="flex gap-3">
        <button 
          onClick={saveEdit} 
          className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
        >
          Save
        </button>
        <button 
          onClick={cancelEdit} 
          className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors"
        >
          Cancel
        </button>
      </div>
    </div>
  ) : (
    <>
      <img 
        src={`${BACKEND_URL}${ad.imageUrl}`} 
        alt={ad.name} 
        className="w-full h-[150px] object-contain" 
      />
      <h3 className="text-lg font-semibold mt-2">{ad.name}</h3>
      <p className="text-gray-600 mt-1">{ad.description}</p>
      <video 
        src={`${BACKEND_URL}${ad.videoUrl}`} 
        className="w-full mt-3 rounded-md" 
        controls 
      />
      
      <div className="mt-10 flex gap-3 justify-between"  style={{ margin: '1.5rem'  }}>
        <button 
          onClick={() => startEdit(ad)}
          className="px-4 py-2 w-20 h-8 bg-yellow-400 text-black rounded-md hover:bg-yellow-500 transition-colors"
        >
          Edit
        </button>
        <button 
          onClick={() => handleDelete(ad._id)}
          className="px-4 py-2  w-20 h-8 bg-red-500 text-white rounded-md hover:bg-red-700 transition-colors"
        >
          Delete
        </button>
      </div>
    </>
  )}
</div>
        ))}
      </div>
    </div>
  );
};

export default AdminPanel;