%code requires {
    #include "nodo.h"
}

%{
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "nodo.h"

void yyerror(const char *s);
int  yylex(void);

void iniciar_modo_grupo(void);
void iniciar_modo_expr(void);
void escanear_cadena(const char *s);
void identificar_grupos(const char *input);
void prefijo(Nodo *n);
void sufijo(Nodo *n);
%}

%union {
    char *texto;
    int   num;
    Nodo *nodo;
}

%token <texto> VARIABLE
%token <texto> LETRA_DIGITO
%token <texto> CUATRO_LETRAS
%token <texto> DIGITOS
%token <texto> CARACTER
%token <texto> DESCONOCIDO
%token <texto> OPERADOR
%token <texto> PUNTUACION

%token <texto> VAR
%token <num>   NUM
%token MAS MENOS POR DIV LPAREN RPAREN

%type <nodo> expr term factor

%left MAS MENOS
%left POR DIV

%%

programa:
    expr  {
        printf("\nArbol:\n");
        imprimir_arbol($1, 0);
        printf("\nPrefijo  : "); prefijo($1); printf("\n");
        printf("Sufijo   : "); sufijo($1);  printf("\n");
    }
;

expr:
    expr MAS   term  { $$ = nuevo_nodo("+", $1, $3); }
  | expr MENOS term  { $$ = nuevo_nodo("-", $1, $3); }
  | term             { $$ = $1; }
;

term:
    term POR factor  { $$ = nuevo_nodo("*", $1, $3); }
  | term DIV factor  { $$ = nuevo_nodo("/", $1, $3); }
  | factor           { $$ = $1; }
;

factor:
    LPAREN expr RPAREN  { $$ = $2; }
  | NUM                 { char buf[32]; sprintf(buf, "%d", $1);
                          $$ = nuevo_nodo(buf, NULL, NULL); }
  | VAR                 { $$ = nuevo_nodo($1, NULL, NULL); }
;

%%

Nodo *nuevo_nodo(const char *val, Nodo *izq, Nodo *der) {
    Nodo *n = (Nodo *)malloc(sizeof(Nodo));
    strncpy(n->valor, val, 63);
    n->valor[63] = '\0';
    n->izq = izq;
    n->der = der;
    return n;
}

void imprimir_arbol(Nodo *n, int nivel) {
    if (n == NULL) return;
    for (int i = 0; i < nivel; i++) printf("  ");
    printf("%s\n", n->valor);
    imprimir_arbol(n->izq, nivel + 1);
    imprimir_arbol(n->der, nivel + 1);
}

void prefijo(Nodo *n) {
    if (n == NULL) return;
    printf("%s ", n->valor);
    prefijo(n->izq);
    prefijo(n->der);
}

void sufijo(Nodo *n) {
    if (n == NULL) return;
    sufijo(n->izq);
    sufijo(n->der);
    printf("%s ", n->valor);
}

void yyerror(const char *s) {
    fprintf(stderr, "Error de sintaxis: %s\n", s);
}

void identificar_grupos(const char *input) {
    int tok;
    iniciar_modo_grupo();
    escanear_cadena(input);
    printf("\nConjunto     Tipo              Lexema\n");
    printf("--------------------------------------\n");
    while ((tok = yylex()) != 0) {
        switch (tok) {
            	case CUATRO_LETRAS: printf("L^4          CUATRO_LETRAS     %s\n", yylval.texto); break;
            	case LETRA_DIGITO:  printf("LD           LETRA_DIGITO      %s\n", yylval.texto); break;
            	case VARIABLE:      printf("L(LUD)*      VARIABLE          %s\n", yylval.texto); break;
            	case DIGITOS:       printf("D+           DIGITOS           %s\n", yylval.texto); break;
            	case CARACTER:      printf("LUD          CARACTER          %s\n", yylval.texto); break;
            	case DESCONOCIDO:   printf("???          DESCONOCIDO       %s\n", yylval.texto); break;
		case OPERADOR:	    printf("OP           OPERADOR          %s\n", yylval.texto); break;
		case PUNTUACION:    printf("PUNT         PUNTUACION        %s\n", yylval.texto); break;
        }
    }
}

int main(int argc, char *argv[]) {
    if (argc < 3) {
        fprintf(stderr, "Uso: lexer <modo> <input>\n");
        return 1;
    }

    char *modo  = argv[1];
    char *input = argv[2];

    if (strcmp(modo, "grupo") == 0) {
        identificar_grupos(input);
    } else if (strcmp(modo, "expr") == 0) {
        iniciar_modo_expr();
        escanear_cadena(input);
        yyparse();
    } else {
        fprintf(stderr, "Modo desconocido: %s\n", modo);
        return 1;
    }

    return 0;
}
