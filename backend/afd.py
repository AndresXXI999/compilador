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

def construir_afn(er):
    estado_count = [0]

    def nuevo_estado():
        estado_count[0] += 1
        return estado_count[0]

    def nfa_simbolo(c):
        s = nuevo_estado()
        a = nuevo_estado()
        return (s, a, {s: {c: [a]}, a: {}})

    def nfa_concat(nfa1, nfa2):
        s1, a1, t1 = nfa1
        s2, a2, t2 = nfa2
        trans = {**t1, **t2}
        if a1 not in trans:
            trans[a1] = {}
        trans[a1]['e'] = trans[a1].get('e', []) + [s2]
        return (s1, a2, trans)

    def nfa_union(nfa1, nfa2):
        s1, a1, t1 = nfa1
        s2, a2, t2 = nfa2
        s = nuevo_estado()
        a = nuevo_estado()
        trans = {**t1, **t2}
        trans[s] = {'e': [s1, s2]}
        if a1 not in trans: trans[a1] = {}
        if a2 not in trans: trans[a2] = {}
        trans[a1]['e'] = trans[a1].get('e', []) + [a]
        trans[a2]['e'] = trans[a2].get('e', []) + [a]
        trans[a] = {}
        return (s, a, trans)

    def nfa_estrella(nfa1):
        s1, a1, t1 = nfa1
        s = nuevo_estado()
        a = nuevo_estado()
        trans = {**t1}
        trans[s] = {'e': [s1, a]}
        if a1 not in trans: trans[a1] = {}
        trans[a1]['e'] = trans[a1].get('e', []) + [s1, a]
        trans[a] = {}
        return (s, a, trans)

    pos = [0]

    def peek():
        return er[pos[0]] if pos[0] < len(er) else None

    def consumir():
        c = er[pos[0]]; pos[0] += 1; return c

    def expr():
        nfa = term()
        while peek() == '|':
            consumir()
            nfa = nfa_union(nfa, term())
        return nfa

    def term():
        nfa = factor()
        while peek() and peek() not in ')|':
            nfa = nfa_concat(nfa, factor())
        return nfa

    def factor():
        nfa = base()
        while peek() == '*':
            consumir()
            nfa = nfa_estrella(nfa)
        return nfa

    def base():
        c = peek()
        if c == '(':
            consumir(); nfa = expr(); consumir(); return nfa
        return nfa_simbolo(consumir())

    start, accept, trans = expr()

    simbolos = set()
    for mov in trans.values():
        simbolos.update(mov.keys())
    simbolos = sorted(simbolos, key=lambda x: (x == 'e', x))

    resultado = []
    resultado.append(f"Estado inicial: q{start}")
    resultado.append(f"Estado de aceptacion: q{accept}")
    resultado.append("")
    resultado.append("Transiciones AFN (e = epsilon):")
    resultado.append(f"{'Estado':<10}" + "".join(f"{s:<14}" for s in simbolos))
    resultado.append("-" * (10 + 14 * len(simbolos)))

    for estado in sorted(trans.keys()):
        nombre = f"q{estado}" + ("*" if estado == accept else "")
        linea = f"{nombre:<10}"
        for sym in simbolos:
            dests = trans[estado].get(sym, [])
            dest_str = "{" + ",".join(f"q{d}" for d in dests) + "}" if dests else "-"
            linea += f"{dest_str:<14}"
        resultado.append(linea)

    return '\n'.join(resultado)


def construir_afn_dot(er):
    estado_count = [0]
    def nuevo_estado():
        estado_count[0] += 1
        return estado_count[0]
    def nfa_simbolo(c):
        s, a = nuevo_estado(), nuevo_estado()
        return (s, a, {s: {c: [a]}, a: {}})
    def nfa_concat(n1, n2):
        s1, a1, t1 = n1; s2, a2, t2 = n2
        trans = {**t1, **t2}
        if a1 not in trans: trans[a1] = {}
        trans[a1]['e'] = trans[a1].get('e', []) + [s2]
        return (s1, a2, trans)
    def nfa_union(n1, n2):
        s1, a1, t1 = n1; s2, a2, t2 = n2
        s, a = nuevo_estado(), nuevo_estado()
        trans = {**t1, **t2}
        trans[s] = {'e': [s1, s2]}
        if a1 not in trans: trans[a1] = {}
        if a2 not in trans: trans[a2] = {}
        trans[a1]['e'] = trans[a1].get('e', []) + [a]
        trans[a2]['e'] = trans[a2].get('e', []) + [a]
        trans[a] = {}
        return (s, a, trans)
    def nfa_estrella(n1):
        s1, a1, t1 = n1
        s, a = nuevo_estado(), nuevo_estado()
        trans = {**t1}
        trans[s] = {'e': [s1, a]}
        if a1 not in trans: trans[a1] = {}
        trans[a1]['e'] = trans[a1].get('e', []) + [s1, a]
        trans[a] = {}
        return (s, a, trans)
    pos = [0]
    def peek(): return er[pos[0]] if pos[0] < len(er) else None
    def consumir(): c = er[pos[0]]; pos[0] += 1; return c
    def expr():
        nfa = term()
        while peek() == '|': consumir(); nfa = nfa_union(nfa, term())
        return nfa
    def term():
        nfa = factor()
        while peek() and peek() not in ')|': nfa = nfa_concat(nfa, factor())
        return nfa
    def factor():
        nfa = base()
        while peek() == '*': consumir(); nfa = nfa_estrella(nfa)
        return nfa
    def base():
        c = peek()
        if c == '(': consumir(); nfa = expr(); consumir(); return nfa
        return nfa_simbolo(consumir())
    start, accept, trans = expr()
    lines = ['digraph {', '  rankdir=LR;',
             '  node [shape=circle fontname="Courier"];',
             '  __i [shape=none label=""];',
             f'  __i -> q{start};',
             f'  q{accept} [shape=doublecircle];']
    for estado, movs in trans.items():
        for sym, dests in movs.items():
            lbl = 'e' if sym == 'e' else sym
            for d in dests:
                lines.append(f'  q{estado} -> q{d} [label="{lbl}"];')
    lines.append('}')
    return '\n'.join(lines)


def construir_afd_dot(er):
    contador_pos[0] = 0
    followpos_tabla.clear()
    arbol = parsear(er)
    calcular(arbol)
    pos_simbolo = {}
    def mapear(nodo):
        if nodo is None: return
        if nodo.tipo == 'hoja': pos_simbolo[nodo.pos] = nodo.valor
        mapear(nodo.izq); mapear(nodo.der)
    mapear(arbol)
    pos_fin = max(pos_simbolo.keys())
    alfabeto = sorted(set(v for v in pos_simbolo.values() if v != '#'))
    estado_inicial = frozenset(arbol.firstpos)
    estados = [estado_inicial]
    transiciones = {}
    visitados = set()
    cola = [estado_inicial]
    while cola:
        estado = cola.pop(0)
        if estado in visitados: continue
        visitados.add(estado)
        transiciones[estado] = {}
        for simbolo in alfabeto:
            siguiente = frozenset(
                p2 for p in estado
                if pos_simbolo.get(p) == simbolo
                for p2 in followpos_tabla.get(p, set())
            )
            if siguiente:
                transiciones[estado][simbolo] = siguiente
                if siguiente not in visitados:
                    cola.append(siguiente)
                    if siguiente not in estados: estados.append(siguiente)
    nombres = {s: f"q{i}" for i, s in enumerate(estados)}
    aceptacion = {s for s in estados if pos_fin in s}
    lines = ['digraph {', '  rankdir=LR;',
             '  node [shape=circle fontname="Courier"];',
             '  __i [shape=none label=""];',
             f'  __i -> {nombres[estado_inicial]};']
    for s in aceptacion:
        lines.append(f'  {nombres[s]} [shape=doublecircle];')
    for estado, movs in transiciones.items():
        for sym, sig in movs.items():
            lines.append(f'  {nombres[estado]} -> {nombres[sig]} [label="{sym}"];')
    tiene_muerto = any(simbolo not in transiciones.get(estado, {}) for estado in estados for simbolo in alfabeto)
    if tiene_muerto:
        lines.append("  qm [shape=circle label=\"qm\"];") 
        for estado in estados:
            for simbolo in alfabeto:
                if simbolo not in transiciones.get(estado, {}):
                    lines.append(f"  {nombres[estado]} -> qm [label=\"{simbolo}\"];")
        for simbolo in alfabeto:
            lines.append(f"  qm -> qm [label=\"{simbolo}\"];")
    lines.append('}')
    return '\n'.join(lines)
