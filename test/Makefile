LIBS	:= 
CARGS	+= -Iinclude -ggdb -Wall -Wextra -pedantic -MMD #-Werror
OUT		:= bin/out

SOURCES		+= main.c token.c ast.c
OBJECTS		:= $(addprefix obj/, $(SOURCES:.c=.o))
DEPS		:= $(OBJECTS:.o=.d)

$(foreach dependency,$(DEPS),$(eval -include $(dependency)))

$(OUT): $(OBJECTS)
	@mkdir -p $(dir ./$(OUT))
	$(CC) $(CARGS) -o ./$(OUT) $^ $(LIBS)

obj/%.o: src/%.c
	@mkdir -p $(dir $@)
	$(CC) -c $(CARGS) -o $@ $<

layout_output:
	python3 -B ../run.py ./src/layout.xml

src/*.c: layout_output

run: $(OUT)
	./$(OUT)

gdb: $(OUT)
	gf2 ./$(OUT)

clean:
	rm -f $(OUT)
	rm -rf ./obj ./bin

.PHONY: run gdb clean