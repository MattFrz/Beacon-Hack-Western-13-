/* beacon_cmd: typed commands for guided (a stand-in for voiced until the mic works).
 *
 *   beacon_cmd                    type commands, one per line
 *   beacon_cmd find my keys       send one command and exit (handy over ssh)
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
#include <string.h>

static beacon_world_t *g_w;

static const char *const k_skip[] = { "find", "where", "is", "are", "my", "the", "a", "an", "go",
                                      "to", "me", "please", "can", "you", "i", "need", "want",
                                      "refill", "get", "for", "some", NULL };
static const struct { const char *word; const char *labels[4]; } k_syn[] = {
    { "water", { "fountain", "dispenser", "sink", "bottle" } },
    { "keys", { "keys", "keychain" } },
    { "key", { "keys", "keychain" } },
    { "cup", { "cup", "mug" } },
    { "coffee", { "mug", "cup" } },
    { "drink", { "bottle", "cup", "can" } },
    { "glasses", { "glasses" } },
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
    printf("sent %s", kind_name(in.kind));
    for (uint32_t i = 0; i < in.n_candidates; ++i)
        printf("%s%s", i ? ", " : " ", in.candidates[i]);
    printf("  (request %u)\n", in.utterance_id);
    fflush(stdout);
    return 0;
}

int main(int argc, char **argv)
{
    g_w = world_open("beacon_cmd");
    if (!g_w)
        return 1;
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
