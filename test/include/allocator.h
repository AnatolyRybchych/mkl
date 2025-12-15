#ifndef ALLOCATOR_H
#define ALLOCATOR_H

typedef struct Allocator Allocator;

struct Allocator {
    void *(*alloc)(Allocator *self, size_t size);
    void (*free)(Allocator *self, void *ptr);
};

#endif // ALLOCATOR_H
