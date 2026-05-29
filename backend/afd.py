# AFD Directo basado en Aho - Metodo de firstpos/lastpos/followpos

class Nodo:
    def __init__(self, tipo, valor=None, izq=None, der=None):
        self.tipo = tipo      # 'hoja', 'concat', 'union', 'estrella'
        self.valor = valor    # solo para hojas
        self.izq = izq
        self.der = der
        self.pos = None       # numero de posicion (solo hojas)
        self.nullable = False
        self.firstpos = set()
        self.lastpos = set()

contador_pos = [0]
followpos_tabla = {}

def nueva_pos():
    contador_pos[0] += 1
    return contador_pos[0]

def calcular(nodo):
    if nodo is None:
        return

    calcular(nodo.izq)
    calcular(nodo.der)

    if nodo.tipo == 'hoja':
        nodo.pos = nueva_pos()
        followpos_tabla[nodo.pos] = set()
        nodo.nullable = (nodo.valor == 'ε')
        nodo.firstpos = {nodo.pos} if not nodo.nullable else set()
        nodo.lastpos  = {nodo.pos} if not nodo.nullable else set()

    elif nodo.tipo == 'union':
        nodo.nullable = nodo.izq.nullable or nodo.der.nullable
        nodo.firstpos = nodo.izq.firstpos | nodo.der.firstpos
        nodo.lastpos  = nodo.izq.lastpos  | nodo.der.lastpos

    elif nodo.tipo == 'concat':
        nodo.nullable = nodo.izq.nullable and nodo.der.nullable
        nodo.firstpos = nodo.izq.firstpos | (nodo.der.firstpos if nodo.izq.nullable else set())
        nodo.lastpos  = nodo.der.lastpos  | (nodo.izq.lastpos  if nodo.der.nullable else set())
        for p in nodo.izq.lastpos:
            followpos_tabla[p] |= nodo.der.firstpos

    elif nodo.tipo == 'estrella':
        nodo.nullable = True
        nodo.firstpos = nodo.izq.firstpos
        nodo.lastpos  = nodo.izq.lastpos
        for p in nodo.izq.lastpos:
            followpos_tabla[p] |= nodo.izq.firstpos

def parsear(er):
    # agrega # al final
    er = er + '#'
    pos = [0]

    def peek():
        if pos[0] < len(er):
            return er[pos[0]]
        return None

    def consumir():
        c = er[pos[0]]
        pos[0] += 1
        return c

    def expr():
        nodo = term()
        while peek() == '|':
            consumir()
            der = term()
            nodo = Nodo('union', izq=nodo, der=der)
        return nodo

    def term():
        nodo = factor()
        while peek() and peek() not in ')|#':
            der = factor()
            nodo = Nodo('concat', izq=nodo, der=der)
        return nodo

    def factor():
        nodo = base()
        while peek() == '*':
            consumir()
            nodo = Nodo('estrella', izq=nodo)
        return nodo

    def base():
        c = peek()
        if c == '(':
            consumir()
            nodo = expr()
            consumir()  # )
            return nodo
        else:
            consumir()
            return Nodo('hoja', valor=c)

    return expr()

def construir_afd(er):
    # resetear
    contador_pos[0] = 0
    followpos_tabla.clear()

    arbol = parsear(er)
    calcular(arbol)

    # mapear posicion a simbolo
    pos_simbolo = {}
    def mapear(nodo):
        if nodo is None: return
        if nodo.tipo == 'hoja':
            pos_simbolo[nodo.pos] = nodo.valor
        mapear(nodo.izq)
        mapear(nodo.der)
    mapear(arbol)

    # encontrar pos del #
    pos_fin = max(pos_simbolo.keys())

    # construir AFD
    alfabeto = sorted(set(v for v in pos_simbolo.values() if v != '#'))
    estado_inicial = frozenset(arbol.firstpos)
    estados = [estado_inicial]
    transiciones = {}
    visitados = set()
    cola = [estado_inicial]

    while cola:
        estado = cola.pop(0)
        if estado in visitados:
            continue
        visitados.add(estado)
        transiciones[estado] = {}

        for simbolo in alfabeto:
            siguiente = frozenset(
                p2
                for p in estado
                if pos_simbolo.get(p) == simbolo
                for p2 in followpos_tabla.get(p, set())
            )
            if siguiente:
                transiciones[estado][simbolo] = siguiente
                if siguiente not in visitados:
                    cola.append(siguiente)
                    if siguiente not in estados:
                        estados.append(siguiente)

    # nombrar estados
    nombres = {s: f"q{i}" for i, s in enumerate(estados)}
    aceptacion = {s for s in estados if pos_fin in s}

    # formatear resultado
    resultado = []
    resultado.append(f"Alfabeto: {{{', '.join(alfabeto)}}}")
    resultado.append(f"Estado inicial: {nombres[estado_inicial]}")
    resultado.append(f"Estados de aceptacion: {{{', '.join(nombres[s] for s in aceptacion)}}}")
    resultado.append("")
    resultado.append("Tabla de transiciones:")
    resultado.append(f"{'Estado':<10}" + "".join(f"{s:<10}" for s in alfabeto))
    resultado.append("-" * (10 + 10 * len(alfabeto)))

    for estado in estados:
        fila = nombres[estado]
        if estado in aceptacion:
            fila += "*"
        linea = f"{fila:<10}"
        for simbolo in alfabeto:
            sig = transiciones[estado].get(simbolo)
            linea += f"{nombres[sig] if sig else 'qm':<10}"
        resultado.append(linea)

    # followpos
    resultado.append("")
    resultado.append("Followpos:")
    for p in sorted(followpos_tabla.keys()):
        resultado.append(f"  pos {p} ({pos_simbolo[p]}): {sorted(followpos_tabla[p])}")

    return '\n'.join(resultado)
