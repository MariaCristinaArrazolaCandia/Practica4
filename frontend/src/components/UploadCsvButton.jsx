import React, { useState } from "react";

const API_URL = "http://localhost:8070/api/upload-csv";

function UploadCsvButton({ onStatusChange }) {
  const [uploading, setUploading] = useState(false);

  const handleUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setUploading(true);

    // Mensaje inicial
    if (onStatusChange) {
      onStatusChange(`Subiendo "${file.name}" al servidor...`);
    }

    try {
      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch(API_URL, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        let detail = `Error HTTP ${res.status}`;
        try {
          const errorData = await res.json();
          if (errorData?.detail) detail = errorData.detail;
        } catch (_) {}
        throw new Error(detail);
      }

      const data = await res.json();
      console.log("Respuesta upload:", data);

      // Mensaje cuando el backend ya aceptó el archivo
      if (onStatusChange) {
        onStatusChange(
          `CSV enviado (${file.name}). El worker está procesando el archivo...`
        );
      }
    } catch (err) {
      console.error("Error al subir CSV:", err);
      if (onStatusChange) {
        onStatusChange(`Error al subir CSV: ${err.message}`);
      }
      alert("Error al subir CSV. Revisa la consola para más detalles.");
    } finally {
      setUploading(false);
      // Permite volver a seleccionar el mismo archivo si se desea
      event.target.value = "";
    }
  };

  return (
    <div className="flex flex-col gap-2">
      <label className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm bg-indigo-600 text-white hover:bg-indigo-700 cursor-pointer">
        <span>{uploading ? "Subiendo..." : "Subir CSV de sonido"}</span>
        <input
          type="file"
          accept=".csv"
          className="hidden"
          onChange={handleUpload}
          disabled={uploading}
        />
      </label>
    </div>
  );
}

export default UploadCsvButton;
