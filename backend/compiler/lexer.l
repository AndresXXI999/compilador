%{
#include "parser.tab.h"
#include <stdlib.h>
#include <string.h>
%}

%x GRUPO

%%

<GRUPO>[a-zA-Z]{4}                { yylval.texto = strdup(yytext); return CUATRO_LETRAS; }
<GRUPO>[a-zA-Z][0-9]              { yylval.texto = strdup(yytext); return LETRA_DIGITO;  }
<GRUPO>[a-zA-Z]([a-zA-Z]|[0-9])+  { yylval.texto = strdup(yytext); return VARIABLE;      }
<GRUPO>[0-9]+                     { yylval.texto = strdup(yytext); return DIGITOS;        }
<GRUPO>[a-zA-Z]                   { yylval.texto = strdup(yytext); return CARACTER;       }
<GRUPO>[0-9]                      { yylval.texto = strdup(yytext); return CARACTER;       }
<GRUPO>[ \t\n]+                   { }
<GRUPO>"+"    { yylval.texto = strdup(yytext); return OPERADOR; }
<GRUPO>"-"    { yylval.texto = strdup(yytext); return OPERADOR; }
<GRUPO>"*"    { yylval.texto = strdup(yytext); return OPERADOR; }
<GRUPO>"/"    { yylval.texto = strdup(yytext); return OPERADOR; }
<GRUPO>"("    { yylval.texto = strdup(yytext); return PUNTUACION; }
<GRUPO>")"    { yylval.texto = strdup(yytext); return PUNTUACION; }
<GRUPO>"|"    { yylval.texto = strdup(yytext); return OPERADOR; }
<GRUPO>"->"   { yylval.texto = strdup(yytext); return PUNTUACION; }
<GRUPO>.                          { yylval.texto = strdup(yytext); return DESCONOCIDO;    }

[a-zA-Z]   { yylval.texto = strdup(yytext); return VAR;    }
[0-9]+     { yylval.num   = atoi(yytext);   return NUM;    }
"+"        { return MAS;    }
"-"        { return MENOS;  }
"*"        { return POR;    }
"/"        { return DIV;    }
"("        { return LPAREN; }
")"        { return RPAREN; }
[ \t\n]+   { }
.          { }

%%

int yywrap(void) { return 1; }

void iniciar_modo_grupo(void) { BEGIN(GRUPO); }
void iniciar_modo_expr(void)  { BEGIN(INITIAL); }
void escanear_cadena(const char *s) { yy_scan_string(s); }
