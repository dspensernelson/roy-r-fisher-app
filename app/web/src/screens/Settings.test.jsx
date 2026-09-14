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
