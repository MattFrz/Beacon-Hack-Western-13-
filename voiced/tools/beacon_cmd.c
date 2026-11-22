/* beacon_cmd: typed commands for guided (a stand-in for voiced until the mic works).
 *
 *   beacon_cmd                    type commands, one per line
 *   beacon_cmd find my keys       send one command and exit (handy over ssh)
 *   beacon_cmd --http [8080]      phone page: open http://<pi>:8080, dictate with the
 *                                 phone keyboard's mic, Send (phone does speech-to-text)
 *
 * Commands (same intents voiced will send):
 *   find|where <thing...>   FIND   e.g. "find bottle", "where are my keys", "find water"
 *   go <thing...>           GO     e.g. "go sink"
 *   stop                    STOP
 *   repeat | again          REPEAT ("say that again")
 *   no | not that one       REJECT (try the next candidate)
 *   back | take me back     RETURN
 * Words are matched to the detector labels (models/labels.txt) with a small
 * synonym table: "water" -> fountain, dispenser, sink, bottle; "keys" -> keys,
 * keychain; "cup" -> cup, mug.
 */
#include "world_shm.h"

#include <ctype.h>
#include <netinet/in.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/time.h>

static beacon_world_t *g_w;
static char g_result[200]; /* last thing sent, for the phone page */

static const char *const k_skip[] = { "find", "where", "is", "are", "my", "the", "a", "an", "go",
                                      "to", "me", "please", "you", "i", "need", "want",
                                      "refill", "get", "for", "some",
                                      /* spoken phrasing from phone dictation: "where's my ...",
                                       * "help me look for ...", "locate the ..." */
                                      "s", "it", "its", "what", "whats", "help", "look", "locate",
                                      "show", "hey", "beacon", "okay", "ok", "of", "and", NULL };
/* `can` used to be a stopword ("can you find..."). It is a demo noun now, so it
 * must reach the intent; the modal reading loses, which is the right trade for
 * "find the can" and only ever costs an extra candidate on "can you find X". */
static const struct { const char *word; const char *labels[4]; } k_syn[] = {
    { "water", { "bottle", "can" } },
    { "key", { "keys" } },
    { "bottle", { "bottle" } },
    { "cans", { "can" } },
};

static int is_skip(const char *w)
{
    for (int i = 0; k_skip[i]; ++i)
        if (!strcmp(w, k_skip[i]))
            return 1;
    return 0;
}

static void add(beacon_intent_t *in, const char *label)
{
    for (uint32_t i = 0; i < in->n_candidates; ++i)
        if (!strcmp(in->candidates[i], label))
            return;
    if (in->n_candidates < BEACON_MAX_CANDIDATES)
        strncpy(in->candidates[in->n_candidates++], label, BEACON_NAME_LEN - 1);
}

static void send_intent(beacon_intent_t *in)
{
    in->t_ns = beacon_now_ns();
    in->utterance_id = g_w->intent.utterance_id + 1; /* single writer: +1 per request */
    beacon_seq_write_begin(&g_w->seq_voiced);
    g_w->intent = *in;
    beacon_seq_write_end(&g_w->seq_voiced);
}

static const char *kind_name(uint32_t k)
{
    static const char *n[] = { "NONE", "FIND", "GO", "RETURN", "STOP", "REPEAT", "REJECT" };
    return k <= BEACON_INTENT_REJECT ? n[k] : "?";
}

/* Returns 0 if understood and sent. */
static int handle(char *line)
{
    for (char *p = line; *p; ++p)
        *p = (char)(ispunct((unsigned char)*p) && *p != '-' ? ' ' : tolower((unsigned char)*p));
    char *words[32];
    int n = 0;
    for (char *t = strtok(line, " \t\r\n"); t && n < 32; t = strtok(NULL, " \t\r\n"))
        words[n++] = t;
    if (n == 0)
        return 1;

    beacon_intent_t in;
    memset(&in, 0, sizeof(in));
    const char *w0 = words[0];
    if (!strcmp(w0, "stop") || !strcmp(w0, "quit") || !strcmp(w0, "cancel"))
        in.kind = BEACON_INTENT_STOP;
    else if (!strcmp(w0, "repeat") || !strcmp(w0, "again") ||
             (n >= 2 && !strcmp(w0, "say") && !strcmp(words[1], "that")))
        in.kind = BEACON_INTENT_REPEAT;
    else if (!strcmp(w0, "no") || !strcmp(w0, "not") || !strcmp(w0, "wrong") || !strcmp(w0, "next"))
        in.kind = BEACON_INTENT_REJECT;
    else if (!strcmp(w0, "back") || !strcmp(w0, "return") ||
             (n >= 2 && !strcmp(w0, "take") && !strcmp(words[n - 1], "back")))
        in.kind = BEACON_INTENT_RETURN;
    else
        in.kind = !strcmp(w0, "go") ? BEACON_INTENT_GO : BEACON_INTENT_FIND;

    if (in.kind == BEACON_INTENT_FIND || in.kind == BEACON_INTENT_GO) {
        /* plain labels first ("water bottle" -> bottle before fountain), then synonyms */
        for (int pass = 0; pass < 2; ++pass)
            for (int i = 0; i < n; ++i) {
                if (is_skip(words[i]))
                    continue;
                int hit = 0;
                for (size_t s = 0; s < sizeof(k_syn) / sizeof(k_syn[0]); ++s)
                    if (!strcmp(words[i], k_syn[s].word)) {
                        hit = 1;
                        if (pass == 1)
                            for (int k = 0; k < 4 && k_syn[s].labels[k]; ++k)
                                add(&in, k_syn[s].labels[k]);
                    }
                if (!hit && pass == 0)
                    add(&in, words[i]); /* already a label, e.g. "bottle", "phone" */
            }
        if (in.n_candidates == 0) {
            fprintf(stderr, "beacon_cmd: find what? e.g. \"find bottle\"\n");
            return 1;
        }
    }
    send_intent(&in);
    {
        size_t k = (size_t)snprintf(g_result, sizeof(g_result), "%s", kind_name(in.kind));
        for (uint32_t i = 0; i < in.n_candidates && k < sizeof(g_result) - 40; ++i)
            k += (size_t)snprintf(g_result + k, sizeof(g_result) - k, "%s%s", i ? ", " : " ", in.candidates[i]);
    }
    printf("sent %s", kind_name(in.kind));
    for (uint32_t i = 0; i < in.n_candidates; ++i)
        printf("%s%s", i ? ", " : " ", in.candidates[i]);
    printf("  (request %u)\n", in.utterance_id);
    fflush(stdout);
    return 0;
}

/* --http [PORT]: a one-page site for a phone on the same Wi-Fi. The phone keyboard's
 * own dictation does the speech-to-text (browsers only allow mic access over HTTPS,
 * keyboards don't care); the words come here and get the same matching as typing. */
static const char k_page_head[] =
    "<!doctype html><html><head><meta charset=utf-8>"
    "<meta name=viewport content='width=device-width,initial-scale=1'>"
    "<title>Beacon</title><style>"
    "body{font:20px system-ui,sans-serif;background:#111;color:#eee;margin:0;padding:24px}"
    "h1{font-size:26px;margin:0 0 6px}p{color:#aaa;margin:0 0 18px}"
    "input{width:100%;box-sizing:border-box;font-size:24px;padding:16px;border-radius:12px;border:2px solid #3ddc84;background:#000;color:#fff}"
    "button{width:100%;margin-top:14px;font-size:24px;padding:16px;border:0;border-radius:12px;background:#3ddc84;color:#000;font-weight:700}"
    ".r{margin-top:22px;font-size:20px;color:#3ddc84}.q{color:#fff}"
    ".b{display:flex;gap:10px;margin-top:14px}.b button{background:#333;color:#eee;margin:0}"
    "</style></head><body><h1>Beacon</h1>"
    "<p>Tap the box, tap the mic on your keyboard, say what you're looking for, then Send.</p>"
    "<form method=post action=/><input name=t autofocus autocomplete=off placeholder=\"where's my water bottle\">"
    "<button>Send</button></form>"
    "<div class=b><form method=post action=/ style='flex:1'><input type=hidden name=t value=repeat><button>Repeat</button></form>"
    "<form method=post action=/ style='flex:1'><input type=hidden name=t value=stop><button>Stop</button></form></div>";

static void url_decode(char *s)
{
    char *o = s;
    for (; *s && *s != '&'; ++s) {
        if (*s == '+') {
            *o++ = ' ';
        } else if (*s == '%' && isxdigit((unsigned char)s[1]) && isxdigit((unsigned char)s[2])) {
            char hex[3] = { s[1], s[2], 0 };
            *o++ = (char)strtol(hex, NULL, 16);
            s += 2;
        } else {
            *o++ = *s;
        }
    }
    *o = '\0';
}

static void html_escape(const char *in, char *out, size_t cap)
{
    size_t n = 0;
    for (; *in && n + 7 < cap; ++in) {
        const char *r = *in == '<' ? "&lt;" : *in == '>' ? "&gt;" : *in == '&' ? "&amp;" : *in == '"' ? "&quot;" : NULL;
        if (r) {
            size_t k = strlen(r);
            memcpy(out + n, r, k);
            n += k;
        } else {
            out[n++] = *in;
        }
    }
    out[n] = '\0';
}

static void send_all(int fd, const char *buf, size_t n)
{
    while (n > 0) {
        ssize_t w = send(fd, buf, n, 0);
        if (w <= 0)
            return;
        buf += w;
        n -= (size_t)w;
    }
}

static int serve_http(int port)
{
    int srv = socket(AF_INET, SOCK_STREAM, 0);
    int one = 1;
    setsockopt(srv, SOL_SOCKET, SO_REUSEADDR, &one, sizeof(one));
    struct sockaddr_in a;
    memset(&a, 0, sizeof(a));
    a.sin_family = AF_INET;
    a.sin_addr.s_addr = htonl(INADDR_ANY);
    a.sin_port = htons((uint16_t)port);
    if (srv < 0 || bind(srv, (struct sockaddr *)&a, sizeof(a)) < 0 || listen(srv, 4) < 0) {
        perror("beacon_cmd: http");
        return 1;
    }
    fprintf(stderr, "beacon_cmd: phone page on http://<this Pi>:%d\n", port);
    for (;;) {
        int c = accept(srv, NULL, NULL);
        if (c < 0)
            continue;
        struct timeval tv = { 2, 0 };
        setsockopt(c, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));
        char req[4096];
        size_t got = 0;
        char *body = NULL;
        long want = 0;
        while (got < sizeof(req) - 1) { /* headers, then Content-Length bytes of body */
            ssize_t n = recv(c, req + got, sizeof(req) - 1 - got, 0);
            if (n <= 0)
                break;
            got += (size_t)n;
            req[got] = '\0';
            if (!body && (body = strstr(req, "\r\n\r\n"))) {
                body += 4;
                const char *cl = strstr(req, "Content-Length:");
                if (!cl)
                    cl = strstr(req, "content-length:");
                want = cl ? strtol(cl + 15, NULL, 10) : 0;
            }
            if (body && (long)(req + got - body) >= want)
                break;
        }
        req[got] = '\0';
        char text[512] = "";
        const char *t = NULL;
        if (!strncmp(req, "POST", 4) && body)
            t = strstr(body, "t=");
        else if (!strncmp(req, "GET /?t=", 8))
            t = req + 6;
        if (t) {
            snprintf(text, sizeof(text), "%s", t + 2);
            char *sp = strpbrk(text, " \r\n");
            if (sp && !strncmp(req, "GET", 3))
                *sp = '\0';
            url_decode(text);
        }
        char result[512] = "";
        if (text[0]) {
            char said[512], esc_said[700], esc_res[400];
            snprintf(said, sizeof(said), "%s", text);
            printf("phone \"%s\" -> ", said);
            g_result[0] = '\0';
            int bad = handle(text);
            html_escape(said, esc_said, sizeof(esc_said));
            html_escape(bad ? "not understood, try \"find bottle\"" : g_result, esc_res, sizeof(esc_res));
            snprintf(result, sizeof(result), "<div class=r>Heard <span class=q>\"%.120s\"</span><br>&rarr; %.150s</div>",
                     esc_said, esc_res);
            fflush(stdout);
        }
        char hdr[160];
        size_t len = strlen(k_page_head) + strlen(result) + strlen("</body></html>");
        snprintf(hdr, sizeof(hdr),
                 "HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\nCache-Control: no-store\r\n"
                 "Content-Length: %zu\r\nConnection: close\r\n\r\n", len);
        send_all(c, hdr, strlen(hdr));
        send_all(c, k_page_head, strlen(k_page_head));
        send_all(c, result, strlen(result));
        send_all(c, "</body></html>", 14);
        close(c);
    }
}

int main(int argc, char **argv)
{
    g_w = world_open("beacon_cmd");
    if (!g_w)
        return 1;
    if (argc > 1 && !strcmp(argv[1], "--http"))
        return serve_http(argc > 2 ? atoi(argv[2]) : 8080);
    if (argc > 1) { /* one-shot: beacon_cmd find my keys */
        char line[512] = "";
        for (int i = 1; i < argc; ++i) {
            strncat(line, argv[i], sizeof(line) - strlen(line) - 2);
            strncat(line, " ", sizeof(line) - strlen(line) - 1);
        }
        return handle(line);
    }
    char line[512];
    fprintf(stderr, "beacon_cmd: type a command (find bottle, stop, repeat, no, back). Ctrl-D to quit.\n> ");
    while (fgets(line, sizeof(line), stdin)) {
        handle(line);
        fprintf(stderr, "> ");
    }
    return 0;
}
