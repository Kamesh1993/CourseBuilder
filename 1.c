#include<stdio.h>
#include<stdlib.h>
void motivational_quote(char msg[])
{
	printf("The motivational_quote is %s\n",msg);
	printf("The size is %i\n",sizeof(msg)));
}

int main()
{
	char quote[] = "Secret of going ahead is getting started";
	motivational_quote(quote);
}