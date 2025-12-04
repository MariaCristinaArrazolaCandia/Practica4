
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
      socket = new WebSocket(wsUrl);

      socket.onopen = () => {
        setWsStatus("conectado");
        // Mantener viva la conexión mandando pings
        socket.send("ping");
      };

      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setLastMessage(data);
          if (onMessage) {
            onMessage(data);
          }
        } catch (err) {
          console.error("Error parseando mensaje WS:", err);
        }
      };

      socket.onerror = (err) => {
        console.error("Error en WebSocket:", err);
        setWsStatus("error");
      };

      socket.onclose = () => {
        setWsStatus("reconectando...");
        reconnectTimeout = setTimeout(connect, 3000);
      };
    };

    connect();

    return () => {
      if (socket && socket.readyState === WebSocket.OPEN) {
        socket.close();
      }
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
      }
    };
  }, [onMessage]);

  // Pequeño indicador flotante (puedes quitarlo si molesta)
  return (
    <div
      style={{
        position: "fixed",
        bottom: 16,
        right: 16,
        padding: "6px 10px",
        backgroundColor:
          wsStatus === "conectado" ? "rgba(22,163,74,0.9)" : "rgba(148,163,184,0.9)",
        color: "white",
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
