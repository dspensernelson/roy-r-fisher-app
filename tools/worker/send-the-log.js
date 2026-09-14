/**
 * The service that receives a log from the app and puts it in front of Spenser.
 *
 * One file, on purpose. It is meant to be pasted whole into the Cloudflare
 * dashboard's Worker editor, because the alternative is a build tool, an
 * account login and a deploy step standing between a defect and a fix. Nothing
 * here is imported from anywhere, and nothing here is bundled.
 *
 * WHAT IT DOES, in order:
 *   1. Refuses anything that is not `POST /send`.
 *   2. Refuses anything over two megabytes by its Content-Length, before the
 *      body is read at all.
 *   3. Reads the body and refuses anything that does not look like one of this
 *      app's logs.
 *   4. Counts: fifty a day globally, five an hour per visitor. Over either, it
 *      refuses with 429 and the app tells her one already arrived this hour.
 *   5. Writes the log into the private R2 bucket. THIS HAPPENS FIRST.
 *   6. Emails it to Spenser with the log attached.
 *
 * WHY THE STORE COMES BEFORE THE EMAIL. Storage is the record and email is the
 * notice. A mail service that is down, rate limited, or refusing an attachment
 * must not be able to lose the only copy of the evidence. If the email fails
 * the log is already in the bucket and the answer says so.
 *
 * WHY THE VISITOR'S ADDRESS IS NEVER STORED. The per-visitor counter needs a
 * name that is the same for the same computer and means nothing to anybody
 * reading the store. So the address is hashed with a secret salt and only the
 * hash becomes a counter name. Nothing in KV identifies a person, and the salt
 * is not in this repository, so the hashes cannot be reversed by guessing
 * addresses either.
 *
 * WHY THE RECIPIENT IS HARD CODED HERE. The app never sends an address. If it
 * did, anybody who downloaded the package, which is public, could point it at
 * a stranger. One address, on this side, out of reach.
 *
 * WHAT MUST BE SET UP IN THE DASHBOARD BEFORE THIS WORKS. None of it is in
 * this repository, and none of it can be:
 *
 *   Bindings
 *     LOGS      R2 bucket binding to the bucket named below. Create the bucket
 *               PRIVATE. It must not have public access and must not have a
 *               development URL.
 *     COUNTERS  Workers KV namespace binding. Any name.
 *
 *   Secrets (Settings, then Variables, added as secrets and never as plain
 *   text, so they are not readable in the dashboard afterwards)
 *     RESEND_KEY    an API key from resend.com
 *     ADDRESS_SALT  any long random string, made once and never changed. It
 *                   only has to be secret and stable.
 *
 *   The bucket's lifecycle rule
 *     Delete objects thirty days after they are created. That is the owner's
 *     decision and it is a dashboard setting rather than code, because an
 *     expiry a Worker enforces only runs when somebody sends something.
 *
 *   The Worker's address
 *     Once it is deployed, paste its address into ENDPOINT in
 *     app/server/sendlog.py. Until that is done the app says so plainly and
 *     tells her to copy the log and email it instead.
 *
 * NOTHING SECRET IS IN THIS FILE and nothing secret may ever be put in it. A
 * test reads it and refuses anything key shaped.
 */

// The one route. It agrees with `sendlog.PATH`; a test holds the two together.
const PATH = "/send";

// Two megabytes, agreeing with `sendlog.MAX_SEND_BYTES`. The app already caps
// a send at one, so reaching this means something is wrong rather than
// something is large.
const MAX_BYTES = 2 * 1024 * 1024;

// What the first line of one of our logs looks like. A prefix rather than the
// whole line, so changing the size of the window does not need a redeploy.
// It agrees with `logwindow.FIRST_LINE`; a test holds the two together.
const MARKER = "Roy R. Fisher,";

// The private bucket. Created private, kept private, thirty day expiry.
const BUCKET_NAME = "rrf-app-logs";

// Fifty a day across everybody, five an hour per visitor. The day cap is the
// backstop: this address is inside a public package, so anybody who downloads
// the app can find it, and the only real protection is that it costs nothing
// and holds nothing worth taking.
const A_DAY = 50;
const AN_HOUR = 5;

// Where it goes. Never sent by the app, and not a parameter of anything.
const TO = "d.spensernelson@gmail.com";

// Resend's shared sending address works without a verified domain and only to
// the account's own address, which is exactly this case. Change it if a domain
// is ever verified.
const FROM = "Roy R. Fisher <onboarding@resend.dev>";

function plain(status, message) {
  return new Response(message + "\n", {
    status: status,
    headers: { "content-type": "text/plain; charset=utf-8" },
  });
}

function stamp(now) {
  return now.toISOString().replace(/[:.]/g, "-");
}

/** A counter name for this visitor that is the same every time and names
 *  nobody. The salt is a secret, so the hashes cannot be worked back to an
 *  address by trying addresses either. */
async function visitorName(request, env) {
  const address = request.headers.get("cf-connecting-ip") || "unknown";
  const material = new TextEncoder().encode(env.ADDRESS_SALT + "|" + address);
  const digest = await crypto.subtle.digest("SHA-256", material);
  const bytes = Array.from(new Uint8Array(digest));
  return bytes.map((b) => b.toString(16).padStart(2, "0")).join("").slice(0, 32);
}

/** Read a counter, and say whether it is already at its ceiling.
 *
 *  KV is eventually consistent, so two sends landing in the same second can
 *  both read the same count. That is understood and accepted: this is a cap
 *  against a runaway loop and an accident, not against somebody determined.
 *  The consequence of it being loose is one extra email. */
async function overCap(env, key, ceiling) {
  const seen = parseInt((await env.COUNTERS.get(key)) || "0", 10);
  return seen >= ceiling;
}

async function countOne(env, key, seconds) {
  const seen = parseInt((await env.COUNTERS.get(key)) || "0", 10);
  await env.COUNTERS.put(key, String(seen + 1), { expirationTtl: seconds });
}

/** Base64 for the attachment, in chunks. Spreading a megabyte of bytes into
 *  String.fromCharCode in one call overflows the argument list. */
function base64(text) {
  const bytes = new TextEncoder().encode(text);
  let binary = "";
  for (let i = 0; i < bytes.length; i += 8192) {
    binary += String.fromCharCode.apply(null, bytes.subarray(i, i + 8192));
  }
  return btoa(binary);
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname !== PATH) {
      return plain(404, "Nothing here.");
    }
    if (request.method !== "POST") {
      return plain(405, "This address only accepts a POST.");
    }

    // Before the body is read. A service that reads two megabytes to decide it
    // did not want them is a service anybody can make expensive.
    const declared = parseInt(request.headers.get("content-length") || "0", 10);
    if (declared > MAX_BYTES) {
      return plain(413, "That is too large to accept.");
    }

    const body = await request.text();
    if (body.length > MAX_BYTES) {
      return plain(413, "That is too large to accept.");
    }
    if (!body.startsWith(MARKER)) {
      // Checked before the counters are touched, on purpose. Otherwise anybody
      // who found this address could spend the day's fifty on rubbish and lock
      // the office out of sending a real log.
      return plain(400, "That is not a Roy R. Fisher log.");
    }

    const now = new Date();
    const dayKey = "day-" + now.toISOString().slice(0, 10);
    const hourKey = "hour-" + (await visitorName(request, env)) + "-"
      + now.toISOString().slice(0, 13);

    if (await overCap(env, dayKey, A_DAY)) {
      return plain(429, "Too many logs have been sent today.");
    }
    if (await overCap(env, hourKey, AN_HOUR)) {
      return plain(429, "A log already arrived from this computer this hour.");
    }

    // The store first. Everything after this can fail without losing the log.
    const name = stamp(now) + ".log";
    try {
      await env.LOGS.put(name, body, {
        httpMetadata: { contentType: "text/plain; charset=utf-8" },
      });
    } catch (err) {
      return plain(500, "The log could not be stored, so nothing was kept.");
    }

    await countOne(env, dayKey, 60 * 60 * 48);
    await countOne(env, hourKey, 60 * 60 * 2);

    let emailed = false;
    try {
      const answer = await fetch("https://api.resend.com/emails", {
        method: "POST",
        headers: {
          "content-type": "application/json",
          authorization: "Bearer " + env.RESEND_KEY,
        },
        body: JSON.stringify({
          from: FROM,
          to: [TO],
          subject: "Roy R. Fisher log, " + now.toISOString().slice(0, 16),
          text: "The last two days of the log from the office copy of the app."
            + "\nStored in " + BUCKET_NAME + " as " + name + "."
            + "\n\nThe first lines of it:\n\n"
            + body.split("\n").slice(0, 12).join("\n"),
          attachments: [{ filename: name, content: base64(body) }],
        }),
      });
      emailed = answer.ok;
    } catch (err) {
      emailed = false;
    }

    // 200 either way, because the log is in the bucket and that is the record.
    // She is told it reached him, and it did. The answer says whether the
    // notice went, for whoever reads the Worker's own log.
    return plain(200, emailed ? "Stored and emailed." : "Stored. The email did not go.");
  },
};
