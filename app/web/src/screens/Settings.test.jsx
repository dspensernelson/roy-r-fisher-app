import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import Settings from "./Settings.jsx";
import * as api from "../api.js";

const WORKSPACE = { path: "C:\\Jobs", folder_count: 4, source: "saved" };

beforeEach(() => {
  vi.spyOn(api, "getSettings").mockResolvedValue({ key_set: true, ends_with: "ab12" });
});

describe("Check now", () => {
  it("tells the rest of the app to look again", async () => {
    // Found 2026-09-03 on Spenser's virtual machine. Check now said "Version
    // 0.6.4 is available. Use the Update available button at the top of the
    // screen" and there was no such button, because the masthead asks the
    // server about updates once at load and nothing told it to ask again.
    vi.spyOn(api, "checkForUpdate").mockResolvedValue({ available: "0.6.4" });
    const onUpdateChecked = vi.fn().mockResolvedValue(undefined);

    render(<Settings workspace={WORKSPACE} version="0.6.3"
                     onChangeFolder={() => {}} onWorkspaceChanged={() => {}}
                     onUpdateChecked={onUpdateChecked} />);
    await userEvent.click(await screen.findByRole("button", { name: "Check now" }));

    expect(await screen.findByText(/Version 0.6.4 is available/)).toBeInTheDocument();
    expect(onUpdateChecked).toHaveBeenCalled();
  });

  it("offers the update beside Check now when it finds one", async () => {
    // Spenser, 2026-09-16: "When Check now finds a version, an Update button
    // appears beside it." The button is the masthead's own, word for word,
    // and it hands back to the handler the masthead uses. The sentence loses
    // its pointer to the top of the screen, because the button is right here.
    vi.spyOn(api, "checkForUpdate").mockResolvedValue({ available: "0.6.4" });
    const onUpdate = vi.fn();

    render(<Settings workspace={WORKSPACE} version="0.6.3"
                     onChangeFolder={() => {}} onWorkspaceChanged={() => {}}
                     onUpdateChecked={() => Promise.resolve()} onUpdate={onUpdate} />);
    const check = await screen.findByRole("button", { name: "Check now" });
    expect(screen.queryByRole("button", { name: "Update available" })).toBeNull();
    await userEvent.click(check);

    const update = await screen.findByRole("button", { name: "Update available" });
    expect(update.parentElement).toBe(check.parentElement);
    expect(update).toHaveClass("button");
    expect(update).not.toHaveClass("linky");
    expect(screen.getByText("Version 0.6.4 is available.")).toBeInTheDocument();
    expect(screen.queryByText(/top of the screen/)).toBeNull();

    await userEvent.click(update);
    expect(onUpdate).toHaveBeenCalledTimes(1);
  });

  it("offers no update button when there is nothing newer", async () => {
    vi.spyOn(api, "checkForUpdate").mockResolvedValue({ available: "" });
    render(<Settings workspace={WORKSPACE} version="0.6.4"
                     onChangeFolder={() => {}} onWorkspaceChanged={() => {}}
                     onUpdate={() => {}} />);
    await userEvent.click(await screen.findByRole("button", { name: "Check now" }));
    await screen.findByText("You are on the newest version.");
    expect(screen.queryByRole("button", { name: "Update available" })).toBeNull();
  });

  it("still works when nothing is listening", async () => {
    vi.spyOn(api, "checkForUpdate").mockResolvedValue({ available: "" });
    render(<Settings workspace={WORKSPACE} version="0.6.4"
                     onChangeFolder={() => {}} onWorkspaceChanged={() => {}} />);
    await userEvent.click(await screen.findByRole("button", { name: "Check now" }));
    expect(await screen.findByText("You are on the newest version.")).toBeInTheDocument();
  });
});

function settings() {
  return render(<Settings workspace={WORKSPACE} version="0.7.0"
                          onChangeFolder={() => {}} onWorkspaceChanged={() => {}} />);
}

const SAMPLE = "Roy R. Fisher, the last 2 days of the log\nLines: 2\n\n" +
  "2026-09-14T09:29:43 GET /api/jobs status=200\n" +
  "2026-09-14T09:30:11 GET /api/jobs/BLAUL/manifest status=400";

describe("Show what will be sent", () => {
  it("shows the text on screen, so nothing leaves unseen", async () => {
    vi.spyOn(api, "logRecent").mockResolvedValue({ text: SAMPLE, lines: 2, empty: false });
    settings();
    await userEvent.click(await screen.findByRole("button", { name: "Show what will be sent" }));
    expect(await screen.findByText(/GET \/api\/jobs\/BLAUL\/manifest/)).toBeInTheDocument();
  });

  it("copies it, so she never has to find a file", async () => {
    vi.spyOn(api, "logRecent").mockResolvedValue({ text: SAMPLE, lines: 2, empty: false });
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, "clipboard", { value: { writeText }, configurable: true });

    settings();
    await userEvent.click(await screen.findByRole("button", { name: "Show what will be sent" }));
    await userEvent.click(await screen.findByRole("button", { name: "Copy" }));

    expect(writeText).toHaveBeenCalledWith(SAMPLE);
    expect(await screen.findByText(/Copied/)).toBeInTheDocument();
  });

  it("tells her how to copy it by hand when the browser refuses", async () => {
    // No dead end, ever. The text is on screen either way, so the way
    // through is always to select it.
    vi.spyOn(api, "logRecent").mockResolvedValue({ text: SAMPLE, lines: 2, empty: false });
    Object.defineProperty(navigator, "clipboard", {
      value: { writeText: vi.fn().mockRejectedValue(new Error("refused")) },
      configurable: true,
    });

    settings();
    await userEvent.click(await screen.findByRole("button", { name: "Show what will be sent" }));
    await userEvent.click(await screen.findByRole("button", { name: "Copy" }));
    expect(await screen.findByText(/select the text/i)).toBeInTheDocument();
  });

  it("says plainly when nothing has been written yet", async () => {
    vi.spyOn(api, "logRecent").mockResolvedValue({
      text: "Roy R. Fisher, the last 2 days of the log\nRead from: nothing",
      lines: 0, empty: true,
    });
    settings();
    await userEvent.click(await screen.findByRole("button", { name: "Show what will be sent" }));
    expect(await screen.findByText(/nothing has been written/i)).toBeInTheDocument();
  });
});

describe("Send the log to Spenser", () => {
  const SENT = "Sent. Spenser has the last two days of the log. You can carry on.";

  it("says it went, in the words the owner approved", async () => {
    vi.spyOn(api, "logSend").mockResolvedValue({ sent: true, message: SENT });
    settings();
    await userEvent.click(await screen.findByRole("button", { name: "Send the log to Spenser" }));
    expect(await screen.findByText(SENT)).toBeInTheDocument();
  });

  it("cannot be pressed twice while it is going", async () => {
    // She pressed the old log button thirteen times in thirty-seven seconds
    // because nothing on screen changed. B7, from the log of 2026-09-02.
    let release;
    vi.spyOn(api, "logSend").mockReturnValue(
      new Promise((resolve) => { release = () => resolve({ sent: true, message: SENT }); }));

    settings();
    await userEvent.click(await screen.findByRole("button", { name: "Send the log to Spenser" }));

    const going = await screen.findByRole("button", { name: "Sending..." });
    expect(going).toBeDisabled();
    expect(screen.queryByRole("button", { name: "Send the log to Spenser" })).toBeNull();

    release();
    expect(await screen.findByText(SENT)).toBeInTheDocument();
  });

  it("shows the server's sentence when it did not go", async () => {
    const refusal = "The log could not be sent. The internet may be off.\n"
      + "You can still get it to him yourself: press Show what will be sent, "
      + "press Copy, and paste it into an email to d.spensernelson@gmail.com.";
    vi.spyOn(api, "logSend").mockResolvedValue({ sent: false, message: refusal });

    settings();
    await userEvent.click(await screen.findByRole("button", { name: "Send the log to Spenser" }));
    expect(await screen.findByText(/paste it into an email/)).toBeInTheDocument();
    // And it can be pressed again. A refusal that leaves the button dead
    // would be the dead end this whole feature exists to remove.
    expect(await screen.findByRole("button", { name: "Send the log to Spenser" }))
      .not.toBeDisabled();
  });

  it("still answers when the app's own server is not there", async () => {
    // The one failure the server cannot word for itself, because it is the
    // server that is missing. Still not a dead end.
    vi.spyOn(api, "logSend").mockRejectedValue(new Error("Failed to fetch"));
    settings();
    await userEvent.click(await screen.findByRole("button", { name: "Send the log to Spenser" }));
    expect(await screen.findByText(/did not answer/)).toBeInTheDocument();
  });
});

// Click 11 of the walk of 2026-09-04, asked again on 2026-09-15: *"why does
// the setting screen still look like 5 panesl down instead of 1 | 2 / 3 | 4 /
// 5 | 6"*.
describe("the cards sit in two columns", () => {
  it("puts every card in one of two columns, in the order he chose", async () => {
    // Superseded on 2026-09-15 by the approved design. This test used to
    // assert five cards with the key card first. `Close the app` left the
    // screen for the nav bar, which is F13, and the owner picked the order
    // of the four that remain card by card. An earlier review argued the key
    // belongs first. He decided otherwise and it is settled.
    settings();
    await screen.findByRole("heading", { name: "Your Anthropic key" });

    const cols = document.querySelectorAll(".settings-grid > .settings-col");
    expect(cols).toHaveLength(2);
    const cards = document.querySelectorAll(".setting");
    expect(cards.length).toBe(4);
    [...cards].forEach((c) => expect(c.parentElement).toHaveClass("settings-col"));

    const heads = [...cols].map((c) => [...c.querySelectorAll("h2")].map((h) => h.textContent));
    expect(heads[0]).toEqual(["The version you are running", "Where your jobs live"]);
    expect(heads[1]).toEqual(["What the app has done", "Your Anthropic key"]);
  });

  it("keeps closing the app off this screen entirely", async () => {
    // F13: no belt and suspenders. It lives in the nav bar now.
    settings();
    await screen.findByRole("heading", { name: "Your Anthropic key" });
    expect(screen.queryByRole("button", { name: "Close the app" })).toBeNull();
    expect(screen.queryByRole("heading", { name: "Closing the app" })).toBeNull();
  });

  it("folds away where the key is kept, on the button row", async () => {
    // Superseded on 2026-09-15 by the approved design. It used to fold away
    // two paragraphs. `What is in it` is deleted: it described the log, and
    // the button beside it shows the log, so the thing beat the description.
    settings();
    const link = await screen.findByRole("button", { name: "Where the key is kept" });
    expect(screen.queryByText(/kept in a file in your own user folder/)).toBeNull();
    // On the button row, pushed right, not on the heading line.
    expect(link.parentElement).toHaveClass("setting-actions");
    await userEvent.click(link);
    expect(screen.getByText(/kept in a file in your own user folder/)).toBeInTheDocument();

    expect(screen.queryByRole("button", { name: "What is in it" })).toBeNull();
  });

  it("says nothing on the key card about what a key is for", async () => {
    // The sentence told him the key costs money. That is said where the money
    // is spent, on the generate window, at the moment he agrees to the figure.
    settings();
    await screen.findByRole("heading", { name: "Your Anthropic key" });
    expect(screen.queryByText(/Two things need a key from Anthropic/)).toBeNull();
    // What he must not lose: the sentence under the title, and the version.
    expect(screen.getByText(/Set this up once/)).toBeInTheDocument();
    expect(screen.getByText(/version 0.7.0/)).toBeInTheDocument();
  });

  it("makes the two jobs-folder controls buttons, and the right two colours", async () => {
    // Spenser, 2026-09-15: *"lets make the 'change jobs' and start 'setup
    // over' buttons instead of linksl"*. The colour law of 2026-09-08 decides
    // which is which: changing the folder can be pointed somewhere else after,
    // so it is filled blue. Starting over cannot be taken back and is not why
    // he came, so it is the plain button with red text.
    settings();
    const change = await screen.findByRole("button", { name: "Change jobs folder" });
    expect(change).toHaveClass("button", "secondary");
    const over = screen.getByRole("button", { name: "Start setup over" });
    expect(over).toHaveClass("button", "final");
  });

  it("makes Show what will be sent a button, knowingly bending the colour rule", async () => {
    // Spenser, 2026-09-15: *"Make this a button like Send the log"*. When
    // sending fails it is the only way the log reaches anybody, and an escape
    // hatch dressed as small print is a fault this app has paid for.
    settings();
    const show = await screen.findByRole("button", { name: "Show what will be sent" });
    expect(show).toHaveClass("button", "secondary");
    expect(show).not.toHaveClass("linky");
  });

  it("says in his words that this computer forces the jobs folder", async () => {
    render(<Settings workspace={{ path: "C:\\Jobs", folder_count: 4, source: "override" }}
                     version="0.7.2" onChangeFolder={() => {}} onWorkspaceChanged={() => {}} />);
    expect(await screen.findByText(/Changing it here will not stick/)).toBeInTheDocument();
    expect(screen.queryByText(/RRF_JOBS_HOME/)).toBeNull();
  });
});
