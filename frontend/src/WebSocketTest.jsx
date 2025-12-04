// frontend/src/WebSocketTest.jsx
import React, { useEffect, useRef, useState } from "react";

const WS_URL = "ws://localhost:8070/ws/notifications";

export default function WebSocketTest() {
  const [messages, setMessages] = useState([]);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef(null);

  useEffect(() => {
    // Crear la conexión WebSocket al montar el componente
    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log("WebSocket conectado ✅");
      setConnected(true);
      // Mensaje inicial de prueba
      ws.send("Hola desde el frontend");
    };

    ws.onmessage = (event) => {
      console.log("Mensaje desde backend:", event.data);
      setMessages((prev) => [...prev, event.data]);
    };

    ws.onclose = () => {
      console.log("WebSocket cerrado ❌");
      setConnected(false);
    };

    ws.onerror = (err) => {
      console.error("Error en WebSocket:", err);
    };

    // Cerrar la conexión al desmontar el componente
    return () => {
      ws.close();
    };
  }, []);

  const handleSend = () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send("Mensaje manual desde el frontend");
    }
  };

  return (
    <div style={{ padding: "1rem", border: "1px solid #ccc", marginTop: "1rem" }}>
      <h3>Prueba WebSocket</h3>
      <p>Estado: {connected ? "Conectado ✅" : "Desconectado ❌"}</p>
      <button onClick={handleSend} disabled={!connected}>
        Enviar mensaje de prueba
      </button>
      <h4>Mensajes recibidos:</h4>
      <ul>
        {messages.map((m, idx) => (
          <li key={idx}>{m}</li>
        ))}
      </ul>
    </div>
  );
}
