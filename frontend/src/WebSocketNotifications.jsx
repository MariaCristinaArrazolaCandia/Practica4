// WebSocketNotifications.jsx
import React, { useEffect, useState } from "react";

const WebSocketNotifications = ({ onMessage }) => {
  const [wsStatus, setWsStatus] = useState("desconectado");
  const [lastMessage, setLastMessage] = useState(null);

  useEffect(() => {
    const protocol = window.location.protocol === "https:" ? "wss://" : "ws://";
    const host = window.location.hostname;
    const port = "8070";
    const wsUrl = `${protocol}${host}:${port}/ws/notifications`;

    let socket;
    let reconnectTimeout;

    const connect = () => {
      console.log("[WS] Conectando a:", wsUrl);
      socket = new WebSocket(wsUrl);

      socket.onopen = () => {
        console.log("[WS] Conectado");
        setWsStatus("conectado");
      };

      socket.onmessage = (event) => {
        console.log("[WS] Mensaje bruto:", event.data);

        let payload;
        try {
          // Intentamos interpretar como JSON (nuestro caso ideal)
          payload = JSON.parse(event.data);
        } catch {
          // Si no es JSON, lo tratamos como texto plano
          payload = { type: "TEXT", text: event.data };
        }

        // Para el badge pequeño, mostramos el texto si existe
        const textForBadge =
          typeof payload === "string"
            ? payload
            : payload.text || JSON.stringify(payload);

        setLastMessage(textForBadge);

        if (onMessage) {
          onMessage(payload);
        }
      };

      socket.onclose = () => {
        console.log("[WS] Desconectado, reintentando en 5s...");
        setWsStatus("desconectado");
        reconnectTimeout = setTimeout(connect, 5000);
      };

      socket.onerror = (err) => {
        console.error("[WS] Error:", err);
        socket.close();
      };
    };

    connect();

    // Cleanup
    return () => {
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
      if (socket && socket.readyState === WebSocket.OPEN) {
        socket.close();
      }
    };
  }, [onMessage]);

  return (
    <div
      style={{
        position: "fixed",
        bottom: 10,
        right: 10,
        backgroundColor: wsStatus === "conectado" ? "#16a34a" : "#dc2626",
        color: "white",
        padding: "6px 10px",
        borderRadius: "999px",
        fontSize: "12px",
        boxShadow: "0 2px 6px rgba(0,0,0,0.25)",
        zIndex: 9999,
      }}
    >
      WS: {wsStatus}
      {lastMessage && (
        <span style={{ marginLeft: 8, fontWeight: "bold" }}>• Nuevo evento</span>
      )}
    </div>
  );
};

export default WebSocketNotifications;
