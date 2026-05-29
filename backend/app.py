from flask import Flask, request, jsonify
from flask_cors import CORS
from afd import construir_afd
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
    return 'cadena'

def evaluar_matematica(expr):
    try:
        resultado = eval(expr.strip())
        return str(resultado)
    except:
        return 'Error en expresion'

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

    elif tipo == 'matematica':
        salida, _ = correr('expr', input_text)
        resultado = evaluar_matematica(input_text)
        fases.append({'fase': 'Lexico', 'resultado': correr('grupo', input_text)[0]})
        fases.append({'fase': 'Sintactico', 'resultado': salida})
        fases.append({'fase': 'Semantico', 'resultado': 'Tipos compatibles: numero op numero'})
        fases.append({'fase': 'Intermedio', 'resultado': f't1 = {input_text}'})
        fases.append({'fase': 'Ensamblador', 'resultado': generar_ensamblador(input_text)})
        fases.append({'fase': 'Resultado', 'resultado': resultado})

    elif tipo == 'er':
        salida, _ = correr('grupo', input_text)
        fases.append({'fase': 'Lexico', 'resultado': salida})
        fases.append({'fase': 'Sintactico', 'resultado': 'Expresion Regular valida'})
        fases.append({'fase': 'AFD', 'resultado': construir_afd(input_text)})

    elif tipo == 'gramatica':
        salida, _ = correr('grupo', input_text)
        fases.append({'fase': 'Lexico', 'resultado': salida})
        fases.append({'fase': 'Sintactico', 'resultado': 'Gramatica identificada'})
        fases.append({'fase': 'Producciones', 'resultado': input_text})

    else:  # cadena
        salida, _ = correr('grupo', input_text)
        fases.append({'fase': 'Lexico', 'resultado': salida})
        fases.append({'fase': 'Sintactico', 'resultado': 'Cadena valida'})
        fases.append({'fase': 'Semantico', 'resultado': 'Tipo: cadena'})

    return jsonify({
        'input': input_text,
        'tipo': tipo,
        'fases': fases
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
