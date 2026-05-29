import { useState } from "react";
import "./App.css";

function App() {
  const [input, setInput] = useState("");
  const [resultado, setResultado] = useState(null);
  const [cargando, setCargando] = useState(false);

  const analizar = async () => {
    if (!input.trim()) return;
    setCargando(true);
    try {
      const res = await fetch("http://127.0.0.1:5000/analizar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ input }),
      });
      const data = await res.json();
      setResultado(data);
    } catch (e) {
      setResultado({ error: "No se pudo conectar al servidor" });
    }
    setCargando(false);
  };

  return (
    <div className="app">
      <h1>Compilador</h1>
      <p className="subtitulo">Ingresa una expresión, cadena, gramática u operación</p>

      <div className="input-area">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && analizar()}
          placeholder="Ej: 2+3, (a|b)*abb, S -> aB | b"
        />
        <button onClick={analizar} disabled={cargando}>
          {cargando ? "Analizando..." : "Analizar"}
        </button>
      </div>

      {resultado && (
        <div className="resultados">
          <div className="tipo">
            Tipo detectado: <span>{resultado.tipo}</span>
          </div>
          {resultado.fases && resultado.fases.map((fase, i) => (
            <div key={i} className="fase">
              <h3>{fase.fase}</h3>
              <pre>{fase.resultado}</pre>
            </div>
          ))}
          {resultado.error && (
            <div className="error">{resultado.error}</div>
          )}
        </div>
      )}
    </div>
  );
}

export default App;
