import { useState, useEffect, useRef } from "react";
import "./App.css";

function GraficaAuto({ dot }) {
  const ref = useRef();
  useEffect(() => {
    import("@viz-js/viz").then(({ instance }) => {
      instance().then(viz => {
        try {
          const svg = viz.renderSVGElement(dot);
          svg.style.maxWidth = "100%";
          svg.style.background = "#fff";
          svg.style.borderRadius = "4px";
          svg.style.padding = "0.5rem";
          if (ref.current) { ref.current.innerHTML = ""; ref.current.appendChild(svg); }
        } catch(e) { if (ref.current) ref.current.textContent = "Error al renderizar"; }
      });
    });
  }, [dot]);
  return <div ref={ref} style={{overflowX:"auto", marginTop:"0.5rem"}} />;
}

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
		<div className="info-bar">
		<span>Tipo: Compilador de múltiples pasadas (Front-end/Back-end)</span>
		<span>•</span>
		<span>Lenguaje: C (Flex + Bison)</span>
		<span>•</span>
		<span>No se almacena información del usuario</span>
		</div>
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

			{resultado.turing && (
				<div className="turing">
				<span>⟩ </span>{resultado.turing}
				</div>
			)}

			{resultado.fases && resultado.fases.map((fase, i) => (
				<div key={i} className="fase">
				<h3>{fase.fase}</h3>
				<pre>{fase.resultado}</pre>
				{fase.dot && <GraficaAuto dot={fase.dot} />}
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

			<div className="fase">
			<h3>Tipos de Tokens</h3>
			<table style={{width:'100%', borderCollapse:'collapse'}}>
			<thead>
			<tr>
			{['Token','Descripción','Ejemplo'].map(h => (
				<th key={h} style={{textAlign:'left', borderBottom:'1px solid #333', padding:'4px 8px', color:'#00ff99'}}>{h}</th>
			))}
			</tr>
			</thead>
			<tbody>
			{[
				['VARIABLE','Letra seguida de letras o dígitos','hello123'],
				['DIGITOS','Uno o más dígitos','99'],
				['CUATRO_LETRAS','Exactamente cuatro letras','hola'],
				['LETRA_DIGITO','Una letra seguida de un dígito','a3'],
				['CARACTER','Una letra o dígito solo','a'],
				['OPERADOR','Operador aritmético o lógico','+'],
				['PUNTUACION','Paréntesis o flecha','('],
				['OFENSA','Palabra inapropiada','...'],
			].map(([tok, desc, ej], i) => (
				<tr key={i}>
				<td style={{padding:'4px 8px', color:'#00ff99'}}>{tok}</td>
				<td style={{padding:'4px 8px'}}>{desc}</td>
				<td style={{padding:'4px 8px'}}>{ej}</td>
				</tr>
			))}
			</tbody>
			</table>
			</div>


			{resultado.error && (
				<div className="error">{resultado.error}</div>
			)}
			</div>
		)}
		</div>
	);
}

export default App;
