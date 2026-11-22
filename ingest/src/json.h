/* json.h: a bounded JSON DOM parser for ingest only.
 *
 * Input is the probe's world-record datagram (one JSON object per
 * datagram/line, a few KB, depth <= 6). The parser is deliberately small
 * and allocation-free: everything is bump-allocated from a caller-provided
 * arena, depth is capped, and malformed or oversized input is rejected
 * with a short static message. It is NOT a general JSON implementation:
 * no surrogate pairs (lone ones become '?'), no numbers longer than 63
 * chars, no use-after-parse outside the arena.
 */
#ifndef INGEST_JSON_H
#define INGEST_JSON_H

#include <stddef.h>
#include <stdint.h>

enum jtype { J_NULL, J_BOOL, J_INT, J_NUM, J_STR, J_ARR, J_OBJ };

typedef struct jval jval;
typedef struct { const char *key; jval *val; } jkv;

struct jval {
    int type;  /* enum jtype */
    int n;     /* J_ARR: item count; J_OBJ: pair count */
    int b;     /* J_BOOL */
    union {
        uint64_t      u;   /* J_INT: non-negative, fits uint64 */
        double        f;   /* J_NUM (also negative integers land here) */
        const char   *s;   /* J_STR: arena, NUL-terminated */
        jval         *items;                          /* J_ARR */
        jkv          *kv;                            /* J_OBJ */
    } v;
};

/* Parses exactly one JSON value covering `len` bytes (NUL terminator not
 * required, trailing garbage rejected). On success returns 0 and stores the
 * root in *root. On failure returns -1; *err points at a short static
 * reason. All returned pointers live inside `arena`. */
int json_parse(const char *text, size_t len, char *arena, size_t arena_size,
               jval **root, const char **err);

/* Accessors. Wrong type or NULL node -> default / NULL. Never crashes. */
int       jis(const jval *v, int type);
jval     *jobj_get(const jval *o, const char *key);   /* NULL if absent */
jval     *jarr_at(const jval *a, int i);               /* NULL if absent */
uint64_t  juint(const jval *v, uint64_t def);
double    jnum(const jval *v, double def);
const char *jstr(const jval *v);                       /* NULL unless J_STR */

#endif /* INGEST_JSON_H */
