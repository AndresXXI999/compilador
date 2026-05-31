from flask import Flask, request, jsonify
# Proyecto desarrollado por lezdoit
# Proyecto desarrollado por lezdoit
from flask_cors import CORS
from afd import construir_afd, construir_afn, construir_afn_dot, construir_afd_dot, arbol_er_dot
import subprocess
import os
import re

app = Flask(__name__)
CORS(app)

COMPILER_DIR = os.path.join(os.path.dirname(__file__), 'compiler')
EJECUTABLE = os.path.join(COMPILER_DIR, 'lexer')

def cargar_ofensas():
    ruta = os.path.join(COMPILER_DIR, 'ofensas.txt')
    with open(ruta, 'r', encoding='utf-8') as f:
        return [linea.strip().lower() for linea in f if linea.strip()]

OFENSAS = cargar_ofensas()
PALABRAS = set()
if os.path.exists(os.path.join(COMPILER_DIR, "palabras.txt")):
    with open(os.path.join(COMPILER_DIR, "palabras.txt"), "r") as f:
        PALABRAS = set(l.strip().lower() for l in f if l.strip())

def compilar():
    result = subprocess.run(['make'], cwd=COMPILER_DIR, capture_output=True, text=True)
    return result.returncode == 0

def correr(modo, input_text):
    if not os.path.exists(EJECUTABLE):
        compilar()
    result = subprocess.run(
            [EJECUTABLE, modo, input_text],
            capture_output=True, text=True, timeout=5
            )
    return result.stdout, result.stderr

def detectar_tipo(input_text):
    texto = input_text.strip().lower()
    for palabra in OFENSAS:
        if palabra in texto:
            return 'ofensa'
    if '->' in input_text or '::=' in input_text:
        return 'gramatica'
    if re.fullmatch(r'[\d\s\+\-\*\/\(\)]+', input_text.strip()):
        return 'matematica'
    if re.search(r'[|*]', input_text) and not re.search(r'\d', input_text):
        return 'er'
    if input_text.isalpha() and len(input_text) > 2:
        if texto in PALABRAS:
            return 'cadena'
        else:
            return 'er'
    return 'cadena'

def evaluar_matematica(expr):
    try:
        resultado = eval(expr.strip())
        return str(resultado)
    except:
        return 'Error en expresion'

def arbol_texto_a_dot(texto):
    lineas = []
    in_tree = False
    for linea in texto.split('\n'):
        if 'Arbol:' in linea:
            in_tree = True
            continue
        if in_tree:
            if linea.strip().startswith('Prefijo') or linea.strip().startswith('Sufijo'):
                break
            if linea.strip():
                lineas.append(linea)
    if not lineas:
        return None
    items = []
    for linea in lineas:
        nivel = (len(linea) - len(linea.lstrip())) // 2
        items.append((nivel, linea.strip()))
    merged = []
    i = 0
    while i < len(items):
        nivel, valor = items[i]
        if valor.startswith('er') and i + 1 < len(items):
            _, op = items[i + 1]
            merged.append((nivel, valor + "\\n" + op, True))
            i += 2
        else:
            merged.append((nivel, valor, False))
            i += 1
    dot_lines = ['digraph {', '  rankdir=TB;', '  node [fontname="Courier" fontsize=14];']
    edges = []
    nid = [0]
    stack = []
    for nivel, valor, interno in merged:
        nid[0] += 1
        curr = nid[0]
        shape = 'ellipse' if interno else 'box'
        dot_lines.append(f'  n{curr} [label="{valor}" shape={shape}];')
        while stack and stack[-1][0] >= nivel:
            stack.pop()
        if stack:
            edges.append(f'  n{stack[-1][1]} -> n{curr};')
        stack.append((nivel, curr))
    dot_lines.extend(edges)
    dot_lines.append('}')
    return '\n'.join(dot_lines)

def generar_ensamblador(expr):
    # tokenizar la expresion
    tokens = re.findall(r'\d+|[+\-*/()]', expr)
    instrucciones = []
    temp = 1
    operandos = []
    operadores = []

    for tok in tokens:
        if re.match(r'\d+', tok):
            operandos.append(tok)
        elif tok in '+-*/':
            operadores.append(tok)

    if len(operandos) >= 2 and len(operadores) >= 1:
        instrucciones.append(f"LOAD  {operandos[0]}")
        for i, op in enumerate(operadores):
            ops = {'+':"ADD", '-':"SUB", '*':"MUL", '/': "DIV"}
            instrucciones.append(f"{ops[op]}   {operandos[i+1]}")
        instrucciones.append(f"STORE t{temp}")
    else:
        instrucciones.append(f"LOAD  {expr}")
        instrucciones.append(f"STORE t{temp}")

    return '\n'.join(instrucciones)

def generar_tabla_simbolos(expr, tipo):
    tabla = []
    if tipo == 'matematica':
        tokens = re.findall(r'\d+', expr)
        for i, tok in enumerate(tokens):
            tabla.append({
                'identificador': f't{i+1}',
                'tipo': 'int',
                'valor': tok,
                'direccion': f'0x{1000 + i*4:04x}'
                })
    elif tipo == 'cadena' or tipo == 'er':
        tokens = re.findall(r'[a-zA-Z]+', expr)
        for i, tok in enumerate(set(tokens)):
            tabla.append({
                'identificador': tok,
                'tipo': 'char',
                'valor': tok,
                'direccion': f'0x{2000 + i*4:04x}'
                })
    elif tipo == 'gramatica':
        # Extrae no terminales (antes de ->) y terminales (después)
        tokens = set()
        partes = expr.split('->')
        if len(partes) == 2:
            izq = partes[0].strip()
            tokens.add(izq)
            der = partes[1].strip()
            for alt in der.split('|'):
                tokens.update(alt.strip().split())
        else:
            tokens = set(expr.split())
        for i, tok in enumerate(sorted(tokens)):
            tabla.append({
                'identificador': tok,
                'tipo': 'NT' if tok.isupper() else 'T',
                'valor': tok,
                'direccion': f'0x{3000 + i*4:04x}'
        })
    return tabla

def turing_respuesta(input_text, tipo):
    if tipo == 'ofensa':
        return "Detecté lenguaje inapropiado. El compilador no puede procesar este tipo de entrada."
    if tipo == 'matematica':
        if re.search(r'[+\-*/]{2,}', input_text):
            return "Detecté operadores consecutivos. ¿Olvidaste un operando?"
        if input_text.count('(') != input_text.count(')'):
            return "Los paréntesis no están balanceados."
        return "Expresión matemática válida. Procesando todas las fases del compilador."
    if tipo == 'er':


        if input_text.endswith('|'):
            return "La expresión regular termina con | sin operando derecho."
        if input_text.endswith('*') or input_text.endswith('+'):
            return "Expresión regular válida con operador de cierre."
        return "Expresión regular válida. Construyendo AFD directo."
    if tipo == 'gramatica':
        return "Gramática libre de contexto detectada. Identificando producciones."
    if re.fullmatch(r"[a-zA-Z]+", input_text.strip()):
        return "Cadena de solo letras. Podria ser una expresion regular simple. Si es una ER, añade operadores."
    return "Cadena de texto detectada. Clasificando segun conjuntos formales."

@app.route('/analizar', methods=['POST'])
def analizar():
    data = request.json
    input_text = data.get('input', '').strip()

    if not input_text:
        return jsonify({'error': 'Input vacio'}), 400

    tipo = detectar_tipo(input_text)
    fases = []

    if tipo == 'ofensa':
        fases.append({'fase': 'Lexico', 'resultado': 'Token OFENSA detectado'})
        fases.append({'fase': 'Respuesta', 'resultado': 'Por favor ingresa una entrada valida.'})
        tabla = generar_tabla_simbolos(input_text, tipo)

    elif tipo == 'matematica':
        salida, _ = correr('expr', input_text)
        resultado = evaluar_matematica(input_text)
        fases.append({'fase': 'Lexico', 'resultado': correr('grupo', input_text)[0]})
        arbol_dot = arbol_texto_a_dot(salida)
        fases.append({'fase': 'Sintactico', 'resultado': salida, 'dot': arbol_dot})
        fases.append({'fase': 'Semantico', 'resultado': 'Tipos compatibles: numero op numero'})
        fases.append({'fase': 'Intermedio', 'resultado': f't1 = {input_text}'})
        fases.append({'fase': 'Ensamblador', 'resultado': generar_ensamblador(input_text)})
        fases.append({'fase': 'Resultado', 'resultado': resultado})
        tabla = generar_tabla_simbolos(input_text, tipo)

    elif tipo == 'er':

        salida, _ = correr('grupo', input_text)
        fases.append({'fase': 'Lexico', 'resultado': salida})
        fases.append({'fase': 'Sintactico', 'resultado': 'Expresion regular valida\nOperadores detectados: union (|), concatenacion, cerradura (*)'})
        fases.append({'fase': 'Arbol Aumentado (ER + #)', 'resultado': 'Arbol de la expresion regular aumentada', 'dot': arbol_er_dot(input_text)})
        fases.append({'fase': 'AFN - Thompson', 'resultado': construir_afn(input_text), 'dot': construir_afn_dot(input_text)})
        fases.append({'fase': 'AFD - Directo', 'resultado': construir_afd(input_text), 'dot': construir_afd_dot(input_text)})
        tabla = generar_tabla_simbolos(input_text, tipo)

    elif tipo == 'gramatica':
        salida, _ = correr('grupo', input_text)
        fases.append({'fase': 'Lexico', 'resultado': salida})
        producciones = []
        partes = input_text.split('->')
        if len(partes) == 2:
            lado_izq = partes[0].strip()
            lado_der = partes[1].strip()
            alternativas = lado_der.split('|')
            for alt in alternativas:
                producciones.append(f"{lado_izq} -> {alt.strip()}")
        fases.append({'fase': 'Sintactico', 'resultado': '\n'.join(producciones) if producciones else 'Gramatica identificada'})
        fases.append({'fase': 'Semantico', 'resultado': f'No terminal: {partes[0].strip() if len(partes) > 0 else "?"}\nProduccion(es): {len(producciones)}'})
        fases.append({'fase': 'BNF', 'resultado': '\n'.join(f'<{p.split("->")[0].strip()}> ::= {p.split("->")[1].strip()}' for p in producciones) if producciones else 'Sin producciones'})
        tabla = generar_tabla_simbolos(input_text, tipo)

    else:  # cadena
        salida, _ = correr('grupo', input_text)
        fases.append({'fase': 'Lexico', 'resultado': salida})
        fases.append({'fase': 'Sintactico', 'resultado': 'Cadena valida'})
        fases.append({'fase': 'Semantico', 'resultado': 'Tipo: cadena'})
        tabla = generar_tabla_simbolos(input_text, tipo)

    return jsonify({
        'input': input_text,
        'tipo': tipo,
        'fases': fases,
        'tabla_simbolos': tabla,
        'turing': turing_respuesta(input_text, tipo)
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
