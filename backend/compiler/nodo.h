#ifndef NODO_H
#define NODO_H

typedef struct Nodo {
    char valor[64];
    struct Nodo *izq;
    struct Nodo *der;
} Nodo;

Nodo *nuevo_nodo(const char *val, Nodo *izq, Nodo *der);
void  imprimir_arbol(Nodo *n, int nivel);

#endif
