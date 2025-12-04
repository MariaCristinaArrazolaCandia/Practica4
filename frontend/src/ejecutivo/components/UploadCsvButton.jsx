import React, { useState } from "react";

/**
 * Props:
 *  - onUploadStart: () => void
 *  - onUploadFinished: (ok: boolean) => void
 */
const UploadCsvButton = ({ onUploadStart, onUploadFinished }) => {
  const [file, setFile] = useState(null);
  const [localStatus, setLocalStatus] = useState("");
  const [loading, setLoading] = useState(false);

  const handleFileChange = (e) => {
    setFile(e.target.files[0] ?? null);
    setLocalStatus("");
  };

  const handleUpload = async () => {
    if (!file) {
      setLocalStatus("Selecciona un archivo CSV primero.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    setLoading(true);
    setLocalStatus("");
    if (onUploadStart) onUploadStart(); // avisamos al Dashboard

    try {
      const response = await fetch("http://localhost:8070/api/upload-csv", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Error al subir CSV");
      }

      const data = await response.json();
      console.log("Respuesta del backend:", data);

      setLocalStatus("CSV enviado. El worker está procesando...");
      setFile(null);
      if (onUploadFinished) onUploadFinished(true);
    } catch (err) {
      console.error(err);
      setLocalStatus("Error al subir el archivo.");
      if (onUploadFinished) onUploadFinished(false);
    }

    setLoading(false);
  };

  return (
    <div className="p-4 border rounded-lg shadow bg-white w-full max-w-lg">
      <h2 className="text-lg font-semibold mb-3">Cargar archivo CSV</h2>

      <input
        type="file"
        accept=".csv"
        className="mb-3 block w-full text-sm"
        onChange={handleFileChange}
      />

      <button
        onClick={handleUpload}
        disabled={loading}
        className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 flex items-center"
      >
        <svg
          className="w-4 h-4 mr-2"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2M7 10l5-5m0 0l5 5m-5-5v12"
          />
        </svg>
        {loading ? "Subiendo..." : "Subir CSV"}
      </button>

      {localStatus && (
        <p className="mt-3 text-sm text-gray-700">{localStatus}</p>
      )}
    </div>
  );
};

export default UploadCsvButton;

