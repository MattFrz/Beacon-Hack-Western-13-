/* json.c: bounded arena JSON parser. See json.h for the contract. */
#include "json.h"

#include <errno.h>
#include <stdlib.h>
#include <string.h>

#define J_MAX_DEPTH   16
#define J_MAX_NUM_LEN 63

typedef struct {
    const char *p, *end;
    char       *arena, *arena_end;
    int         depth;
    const char *err;
} jparser;

static void *jalloc(jparser *s, size_t n)
{
    n = (n + 7u) & ~(size_t)7u;
    if (n > (size_t)(s->arena_end - s->arena)) {
        s->err = "arena exhausted";
        return NULL;
    }
    void *out = s->arena;
    s->arena += n;
    return out;
}

static jval *jnew(jparser *s, int type)
{
    jval *v = jalloc(s, sizeof(*v));
    if (v) {
        v->type = type;
        v->n = 0;
        v->b = 0;
        v->v.u = 0; /* zeroes the whole union */
    }
    return v;
}

static void skip_ws(jparser *s)
{
    while (s->p < s->end &&
           (*s->p == ' ' || *s->p == '\t' || *s->p == '\n' || *s->p == '\r'))
        ++s->p;
}

/* Parses a string starting at the opening quote. The bytes are emitted
 * directly into the arena (unescaped, NUL-terminated). */
static char *jstring(jparser *s)
{
    if (s->p == s->end || *s->p != '"') {
        s->err = "expected string";
        return NULL;
    }
    ++s->p;
    char *out = s->arena;
    char *w = out;
    while (s->p < s->end) {
        unsigned char c = (unsigned char)*s->p++;
        if (c == '"') {
            if (w == s->arena_end) {
                s->err = "arena exhausted";
                return NULL;
            }
            *w = '\0';
            s->arena = w + 1;
            return out;
        }
        if (c == '\\') {
            if (s->p == s->end) {
                s->err = "unterminated escape";
                return NULL;
            }
            char e = *s->p++;
            switch (e) {
            case '"': case '\\': case '/':  *w++ = e;    break;
            case 'b':                       *w++ = '\b'; break;
            case 'f':                       *w++ = '\f'; break;
            case 'n':                       *w++ = '\n'; break;
            case 'r':                       *w++ = '\r'; break;
            case 't':                       *w++ = '\t'; break;
            case 'u': {
                if (s->end - s->p < 4) {
                    s->err = "short \\u escape";
                    return NULL;
                }
                unsigned cp = 0;
                for (int i = 0; i < 4; ++i) {
                    char h = *s->p++;
                    cp <<= 4;
                    if (h >= '0' && h <= '9')      cp |= (unsigned)(h - '0');
                    else if (h >= 'a' && h <= 'f') cp |= (unsigned)(h - 'a' + 10);
                    else if (h >= 'A' && h <= 'F') cp |= (unsigned)(h - 'A' + 10);
                    else { s->err = "bad \\u escape"; return NULL; }
                }
                /* Minimal UTF-8 emit; lone surrogates (never sent by the
                 * probe) collapse to '?'. */
                if (cp >= 0xd800 && cp <= 0xdfff)
                    *w++ = '?';
                else if (cp < 0x80)
                    *w++ = (char)cp;
                else if (cp < 0x800) {
                    if (w + 2 > s->arena_end) { s->err = "arena exhausted"; return NULL; }
                    *w++ = (char)(0xc0 | (cp >> 6));
                    *w++ = (char)(0x80 | (cp & 0x3f));
                } else {
                    if (w + 3 > s->arena_end) { s->err = "arena exhausted"; return NULL; }
                    *w++ = (char)(0xe0 | (cp >> 12));
                    *w++ = (char)(0x80 | ((cp >> 6) & 0x3f));
                    *w++ = (char)(0x80 | (cp & 0x3f));
                }
                break;
            }
            default:
                s->err = "bad escape";
                return NULL;
            }
        } else {
            *w++ = (char)c;
        }
        if (w == s->arena_end) {
            s->err = "arena exhausted";
            return NULL;
        }
    }
    s->err = "unterminated string";
    return NULL;
}

static jval *jvalue(jparser *s);

static jval *jnumber(jparser *s)
{
    char buf[J_MAX_NUM_LEN + 1];
    size_t len = 0;
    int is_int = 1;
    if (s->p != s->end && (*s->p == '-' || *s->p == '+'))
        buf[len++] = *s->p++;
    while (s->p < s->end) {
        char c = *s->p;
        if ((c >= '0' && c <= '9') || c == '.' || c == 'e' || c == 'E' ||
            c == '-' || c == '+') {
            if (c == '.' || c == 'e' || c == 'E')
                is_int = 0;
            if (len == J_MAX_NUM_LEN) {
                s->err = "number too long";
                return NULL;
            }
            buf[len++] = *s->p++;
        } else {
            break;
        }
    }
    if (len == 0) {
        s->err = "expected number";
        return NULL;
    }
    buf[len] = '\0';
    jval *v;
    if (is_int && buf[0] != '-' && buf[0] != '+') {
        errno = 0;
        char *endp = NULL;
        unsigned long long u = strtoull(buf, &endp, 10);
        if (errno != 0 || endp != buf + len) {
            s->err = "bad integer";
            return NULL;
        }
        v = jnew(s, J_INT);
        if (!v)
            return NULL;
        v->v.u = (uint64_t)u;
    } else {
        char *endp = NULL;
        double f = strtod(buf, &endp);
        if (endp != buf + len) {
            s->err = "bad number";
            return NULL;
        }
        v = jnew(s, J_NUM);
        if (!v)
            return NULL;
        v->v.f = f;
    }
    return v;
}

static jval *jarray(jparser *s)
{
    jval *a = jnew(s, J_ARR);
    if (!a)
        return NULL;
    jval *items = NULL;
    int cap = 0;
    ++s->p; /* '[' */
    skip_ws(s);
    if (s->p < s->end && *s->p == ']') {
        ++s->p;
        a->v.items = items; /* NULL, n == 0 */
        return a;
    }
    for (;;) {
        jval *item = jvalue(s);
        if (!item)
            return NULL;
        if (a->n == cap) {
            int ncap = cap ? cap * 2 : 8;
            jval *grown = jalloc(s, (size_t)ncap * sizeof(jval));
            if (!grown)
                return NULL;
            if (cap)
                memcpy(grown, items, (size_t)cap * sizeof(*items));
            items = grown;
            cap = ncap;
        }
        items[a->n] = *item; /* array of values; inner pointers are arena-owned */
        ++a->n;
        skip_ws(s);
        if (s->p < s->end && *s->p == ',') {
            ++s->p;
            continue;
        }
        if (s->p < s->end && *s->p == ']') {
            ++s->p;
            a->v.items = items;
            return a;
        }
        s->err = "expected , or ]";
        return NULL;
    }
}

static jval *jobject(jparser *s)
{
    jval *o = jnew(s, J_OBJ);
    if (!o)
        return NULL;
    jkv *kv = NULL;
    int cap = 0;
    ++s->p; /* '{' */
    skip_ws(s);
    if (s->p < s->end && *s->p == '}') {
        ++s->p;
        o->v.kv = kv; /* NULL, n == 0 */
        return o;
    }
    for (;;) {
        skip_ws(s);
        char *key = jstring(s);
        if (!key)
            return NULL;
        skip_ws(s);
        if (s->p == s->end || *s->p != ':') {
            s->err = "expected ':'";
            return NULL;
        }
        ++s->p;
        jval *val = jvalue(s);
        if (!val)
            return NULL;
        if (o->n == cap) {
            int ncap = cap ? cap * 2 : 8;
            jkv *grown = jalloc(s, (size_t)ncap * sizeof(jkv));
            if (!grown)
                return NULL;
            if (cap)
                memcpy(grown, kv, (size_t)cap * sizeof(*kv));
            kv = grown;
            cap = ncap;
        }
        kv[o->n].key = key;
        kv[o->n].val = val;
        ++o->n;
        skip_ws(s);
        if (s->p < s->end && *s->p == ',') {
            ++s->p;
            continue;
        }
        if (s->p < s->end && *s->p == '}') {
            ++s->p;
            o->v.kv = kv;
            return o;
        }
        s->err = "expected , or }";
        return NULL;
    }
}

static jval *jvalue(jparser *s)
{
    if (s->depth >= J_MAX_DEPTH) {
        s->err = "nesting too deep";
        return NULL;
    }
    skip_ws(s);
    if (s->p == s->end) {
        s->err = "unexpected end";
        return NULL;
    }
    char c = *s->p;
    if (c == '{') {
        ++s->depth;
        jval *v = jobject(s);
        --s->depth;
        return v;
    }
    if (c == '[') {
        ++s->depth;
        jval *v = jarray(s);
        --s->depth;
        return v;
    }
    if (c == '"') {
        jval *v = jnew(s, J_STR);
        if (!v)
            return NULL;
        char *str = jstring(s);
        if (!str)
            return NULL;
        v->v.s = str;
        return v;
    }
    if (c == 't' && (size_t)(s->end - s->p) >= 4 && memcmp(s->p, "true", 4) == 0) {
        s->p += 4;
        jval *v = jnew(s, J_BOOL);
        if (!v)
            return NULL;
        v->b = 1;
        return v;
    }
    if (c == 'f' && (size_t)(s->end - s->p) >= 5 && memcmp(s->p, "false", 5) == 0) {
        s->p += 5;
        return jnew(s, J_BOOL);
    }
    if (c == 'n' && (size_t)(s->end - s->p) >= 4 && memcmp(s->p, "null", 4) == 0) {
        s->p += 4;
        return jnew(s, J_NULL);
    }
    return jnumber(s);
}

int json_parse(const char *text, size_t len, char *arena, size_t arena_size,
               jval **root, const char **err)
{
    if (!text || !arena || !root || !err)
        return -1;
    *root = NULL;
    *err = "";
    jparser s = { .p = text, .end = text + len,
                  .arena = arena, .arena_end = arena + arena_size,
                  .depth = 0, .err = NULL };
    jval *v = jvalue(&s);
    if (!v) {
        *err = s.err ? s.err : "parse error";
        return -1;
    }
    skip_ws(&s);
    if (s.p != s.end) {
        *err = "trailing garbage";
        return -1;
    }
    *root = v;
    return 0;
}

/* ------------------------------------------------------------------ accessors */

int jis(const jval *v, int type)
{
    return v && v->type == type;
}

jval *jobj_get(const jval *o, const char *key)
{
    if (!jis(o, J_OBJ))
        return NULL;
    for (int i = 0; i < o->n; ++i)
        if (strcmp(o->v.kv[i].key, key) == 0)
            return o->v.kv[i].val;
    return NULL;
}

jval *jarr_at(const jval *a, int i)
{
    if (!jis(a, J_ARR) || i < 0 || i >= a->n)
        return NULL;
    return &a->v.items[i];
}

uint64_t juint(const jval *v, uint64_t def)
{
    if (jis(v, J_INT))
        return v->v.u;
    if (jis(v, J_NUM) && v->v.f >= 0.0 && v->v.f < 18446744073709551616.0)
        return (uint64_t)v->v.f;
    if (jis(v, J_BOOL))
        return v->b ? 1u : 0u; /* the probe sends booleans (valid, in_latest_boxes) */
    return def;
}

double jnum(const jval *v, double def)
{
    if (jis(v, J_NUM))
        return v->v.f;
    if (jis(v, J_INT))
        return (double)v->v.u;
    if (jis(v, J_BOOL))
        return v->b ? 1.0 : 0.0;
    return def;
}

const char *jstr(const jval *v)
{
    return jis(v, J_STR) ? v->v.s : NULL;
}
