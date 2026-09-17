import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";

import UpdateStep, { megabytes } from "./UpdateStep.jsx";
import * as api from "../api.js";

const SIZE = 55939858;   // the real v0.5.3 package, 53 MB

function open(over = {}) {
  return render(<UpdateStep version="0.5.3" available="0.5.4" size={SIZE}
                            onClose={() => {}} {...over} />);
}

function progress(over = {}) {
  return { running: true, stage: "Downloading", done: 0, total: SIZE,
           error: "", version: "0.5.4", cancelling: false, ...over };
}

beforeEach(() => { vi.restoreAllMocks(); });

describe("what he is told before he agrees", () => {
  it("names the version and what the download costs", () => {
    open();
    expect(screen.getByText(/Update to version 0\.5\.4\?/)).toBeInTheDocument();
    expect(screen.getByText(/about 53 MB/)).toBeInTheDocument();
    expect(screen.getByText(/You are on version 0\.5\.3/)).toBeInTheDocument();
  });

  it("says the app restarts and his settings stay, in his words", () => {
    // Spenser's own wording, 2026-09-17. The paragraph about what the check
    // proves is gone at his request: three words, not ten.
    const { container } = open();
    const text = container.textContent.replace(/\s+/g, " ");
    expect(text).toContain(
      "You are on version 0.5.3. The download is about 53 MB. The app closes " +
      "itself and opens again as a new version. Your settings remain the same.");
    expect(text).not.toMatch(/exactly what was published/);
    expect(text).not.toMatch(/not kept inside the app/);
    expect(screen.queryByText(/checksum/i)).toBeNull();
  });

  it("does not start anything until he clicks", () => {
    const start = vi.spyOn(api, "startUpdate");
    open();
    expect(start).not.toHaveBeenCalled();
  });

  it("Not now closes the step and starts nothing", async () => {
    const start = vi.spyOn(api, "startUpdate");
    const closed = vi.fn();
    open({ onClose: closed });
    await userEvent.click(screen.getByRole("button", { name: "Not now" }));
    expect(closed).toHaveBeenCalled();
    expect(start).not.toHaveBeenCalled();
  });
});

describe("while it runs", () => {
  it("shows megabytes of the total rather than a bar that says nothing", async () => {
    vi.spyOn(api, "startUpdate").mockResolvedValue({});
    vi.spyOn(api, "updateProgress").mockResolvedValue(
      progress({ done: 12 * 1024 * 1024 }));
    open();
    await userEvent.click(screen.getByRole("button", { name: "Update now" }));
    await waitFor(() =>
      expect(screen.getByText("Downloading 12 MB of 53 MB")).toBeInTheDocument());
  });

  it("names each stage in words", async () => {
    vi.spyOn(api, "startUpdate").mockResolvedValue({});
    vi.spyOn(api, "updateProgress").mockResolvedValue(
      progress({ stage: "Checking the download" }));
    open();
    await userEvent.click(screen.getByRole("button", { name: "Update now" }));
    await waitFor(() =>
      expect(screen.getByText("Checking the download")).toBeInTheDocument());
  });

  it("offers a Cancel while it is downloading", async () => {
    vi.spyOn(api, "startUpdate").mockResolvedValue({});
    vi.spyOn(api, "updateProgress").mockResolvedValue(progress());
    const cancel = vi.spyOn(api, "cancelUpdate").mockResolvedValue({});
    open();
    await userEvent.click(screen.getByRole("button", { name: "Update now" }));
    await waitFor(() => screen.getByRole("button", { name: "Cancel" }));
    await userEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(cancel).toHaveBeenCalled();
  });

  it("does not offer a Cancel once it has moved past the download", async () => {
    vi.spyOn(api, "startUpdate").mockResolvedValue({});
    vi.spyOn(api, "updateProgress").mockResolvedValue(
      progress({ stage: "Installing" }));
    open();
    await userEvent.click(screen.getByRole("button", { name: "Update now" }));
    await waitFor(() => screen.getByText("Installing"));
    expect(screen.queryByRole("button", { name: "Cancel" })).toBeNull();
  });
});

describe("how it ends", () => {
  it("waits quietly and promises nothing it cannot know", async () => {
    // Before 2026-09-16 this tab was a dead end. It said "You can close this
    // tab" and named a new tab that might never exist, because the app came
    // back on a port the operating system had picked and this page had no
    // way to learn it. The app now answers on the same number every time, so
    // this page waits and becomes the new version itself.
    vi.spyOn(api, "startUpdate").mockResolvedValue({});
    vi.spyOn(api, "updateProgress").mockResolvedValue(
      progress({ running: false, stage: "Closing" }));
    open();
    await userEvent.click(screen.getByRole("button", { name: "Update now" }));
    await waitFor(() => expect(
      screen.getByText("Installing the new version.")).toBeInTheDocument());

    expect(screen.getByText(/comes back on its own/)).toBeInTheDocument();
    // Nothing about closing it, and nothing about another tab. Those were the
    // two claims it could not stand behind.
    expect(screen.queryByText(/You can close this tab/)).toBeNull();
    expect(screen.queryByText(/new tab/)).toBeNull();
    expect(screen.queryByText(/not answering/)).toBeNull();
  });

  it("becomes the new version when a different one answers", async () => {
    vi.spyOn(api, "startUpdate").mockResolvedValue({});
    vi.spyOn(api, "updateProgress").mockResolvedValue(
      progress({ running: false, stage: "Closing" }));
    const went = [];
    const replace = vi.fn();
    vi.stubGlobal("fetch", (url) => {
      went.push(String(url));
      if (String(url).includes("/api/version")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ version: "9.9.9" }) });
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
    });
    const where = window.location;
    delete window.location;
    window.location = { replace };

    open();
    await userEvent.click(screen.getByRole("button", { name: "Update now" }));
    await waitFor(() => expect(replace).toHaveBeenCalledWith("/"), { timeout: 4000 });

    // It announces itself on the way past, on the same route the loading page
    // uses, so the new app does not open a tab beside this one.
    expect(went.some((u) => u.includes("/api/loading-page"))).toBe(true);
    window.location = where;
    vi.unstubAllGlobals();
  });

  it("does not become a version that is the one already running", async () => {
    // The old app answers right up until it goes. Reloading into it would put
    // her back exactly where she started, on a page about to die again.
    vi.spyOn(api, "startUpdate").mockResolvedValue({});
    vi.spyOn(api, "updateProgress").mockResolvedValue(
      progress({ running: false, stage: "Closing" }));
    const replace = vi.fn();
    vi.stubGlobal("fetch", () => Promise.resolve({
      ok: true, json: () => Promise.resolve({ version: "0.5.3" }) }));
    const where = window.location;
    delete window.location;
    window.location = { replace };

    open();
    await userEvent.click(screen.getByRole("button", { name: "Update now" }));
    await new Promise((r) => setTimeout(r, 1500));
    expect(replace).not.toHaveBeenCalled();

    window.location = where;
    vi.unstubAllGlobals();
  });

  it("shows a failure as one sentence he can read", async () => {
    vi.spyOn(api, "startUpdate").mockResolvedValue({});
    vi.spyOn(api, "updateProgress").mockResolvedValue(progress({
      running: false, stage: "",
      error: "The update did not arrive intact and was not installed." }));
    open();
    await userEvent.click(screen.getByRole("button", { name: "Update now" }));
    await waitFor(() => expect(
      screen.getByText(/did not arrive intact/)).toBeInTheDocument());
    expect(screen.getByRole("button", { name: "Close" })).toBeInTheDocument();
  });

  it("shows a refusal to start as one sentence", async () => {
    vi.spyOn(api, "startUpdate").mockRejectedValue(
      new Error("An update is already running."));
    open();
    await userEvent.click(screen.getByRole("button", { name: "Update now" }));
    await waitFor(() => expect(
      screen.getByText("An update is already running.")).toBeInTheDocument());
  });

  it("treats the app going quiet as the ending it asked for", async () => {
    // The successful ending is the app closing itself, so the last poll before
    // it goes will not answer. That is not an error to put on his screen.
    vi.spyOn(api, "startUpdate").mockResolvedValue({});
    vi.spyOn(api, "updateProgress")
      .mockResolvedValueOnce(progress({ running: false, stage: "Closing" }))
      .mockRejectedValue(new Error("Failed to fetch"));
    open();
    await userEvent.click(screen.getByRole("button", { name: "Update now" }));
    await waitFor(() => screen.getByText("Installing the new version."));
    expect(screen.queryByText(/Failed to fetch/)).toBeNull();
  });
});

describe("megabytes", () => {
  it("reads the real package as 53 MB", () => {
    expect(megabytes(SIZE)).toBe("53 MB");
  });

  it("says nothing rather than nonsense when there is no size", () => {
    expect(megabytes(0)).toBe("");
    expect(megabytes(undefined)).toBe("");
    expect(megabytes(-1)).toBe("");
  });
});
