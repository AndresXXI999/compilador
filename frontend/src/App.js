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

	{resultado.tabla_simbolos && resultado.tabla_simbolos.length > 0 && (
  	<div className="fase">
    	<h3>Tabla de Símbolos</h3>
    	<table style={{width:'100%', borderCollapse:'collapse'}}>
      	<thead>
        	<tr>
          	{['Identificador','Tipo','Valor','Dirección'].map(h => (
            	<th key={h} style={{textAlign:'left', borderBottom:'1px solid #333', padding:'4px 8px', color:'#00ff99'}}>{h}</th>
          	))}
        	</tr>
      	</thead>
      	<tbody>
        	{resultado.tabla_simbolos.map((s, i) => (
          	<tr key={i}>
            	<td style={{padding:'4px 8px'}}>{s.identificador}</td>
            	<td style={{padding:'4px 8px'}}>{s.tipo}</td>
            	<td style={{padding:'4px 8px'}}>{s.valor}</td>
            	<td style={{padding:'4px 8px'}}>{s.direccion}</td>
          	</tr>
        	))}
      	</tbody>
    	</table>
  	</div>
	)}

          {resultado.error && (
            <div className="error">{resultado.error}</div>
          )}
        </div>
      )}
    </div>
  );
}

export default App;
