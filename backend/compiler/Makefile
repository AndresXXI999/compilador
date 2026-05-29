CC     = gcc
CFLAGS = -Wall -Wno-unused-function

all: lexer

lexer: parser.tab.c lex.yy.c
	$(CC) $(CFLAGS) parser.tab.c lex.yy.c -o lexer

parser.tab.c parser.tab.h: parser.y
	bison -d parser.y

lex.yy.c: lexer.l parser.tab.h
	flex lexer.l

clean:
	rm -f parser.tab.c parser.tab.h lex.yy.c lexer
