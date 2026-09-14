import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";

import App from "./App.jsx";
import * as api from "./api.js";

const WORKSPACE = { valid: true, chosen: true, path: "/jobs", folder_count: 2,
                    source: "saved" };

function quiet(over = {}) {
  vi.spyOn(api, "getWorkspace").mockResolvedValue(WORKSPACE);
  vi.spyOn(api, "getDemo").mockResolvedValue({ demo_mode: false });
  vi.spyOn(api, "appVersion").mockResolvedValue({ version: "0.5.3" });
  vi.spyOn(api, "listJobs").mockResolvedValue([]);
  vi.spyOn(api, "updateStatus").mockResolvedValue({
    version: "0.5.3", available: "", size: 0, looked: true,
    run: { running: false, stage: "", done: 0, total: 0, error: "" },
    ...over,
  });
}

beforeEach(() => {
  vi.restoreAllMocks();
  sessionStorage.clear();
});

describe("the notice in the masthead", () => {
  it("shows only the version when there is nothing to offer", async () => {
    quiet();
    render(<App />);
    await waitFor(() => expect(screen.getByText("v0.5.3")).toBeInTheDocument());
    expect(screen.queryByRole("button", { name: "Update available" })).toBeNull();
  });

  it("shows nothing when the bucket could not be reached", async () => {
    // No internet and a bucket that is down are not things Mark can act on, so
    // they look exactly like there being no update.
    quiet();
    vi.spyOn(api, "updateStatus").mockRejectedValue(new Error("Failed to fetch"));
    render(<App />);
    await waitFor(() => expect(screen.getByText("v0.5.3")).toBeInTheDocument());
    expect(screen.queryByRole("button", { name: "Update available" })).toBeNull();
  });

  it("offers the update when one is known", async () => {
    quiet({ available: "0.5.4", size: 55939858 });
    render(<App />);
    await waitFor(() =>
      screen.getByRole("button", { name: "Update available" }));
  });

  it("asks the question inside the action rather than beside it", async () => {
    // Nothing about updating is on the screen until he clicks the notice.
    quiet({ available: "0.5.4", size: 55939858 });
    render(<App />);
    const notice = await screen.findByRole("button", { name: "Update available" });
    expect(screen.queryByText(/Update to version 0\.5\.4\?/)).toBeNull();
    await userEvent.click(notice);
    expect(screen.getByText(/Update to version 0\.5\.4\?/)).toBeInTheDocument();
    expect(screen.getByText(/about 53 MB/)).toBeInTheDocument();
  });

  it("closes again on Not now, leaving the app where it was", async () => {
    quiet({ available: "0.5.4", size: 55939858 });
    render(<App />);
    await userEvent.click(
      await screen.findByRole("button", { name: "Update available" }));
    await userEvent.click(screen.getByRole("button", { name: "Not now" }));
    expect(screen.queryByText(/Update to version 0\.5\.4\?/)).toBeNull();
    expect(screen.getByRole("button", { name: "Update available" }))
      .toBeInTheDocument();
  });

  it("never looks for an update itself", async () => {
    // The look happens once in the background when the app starts. Opening a
    // screen must not cost a request to the internet.
    quiet({ available: "0.5.4", size: 55939858 });
    const look = vi.spyOn(api, "checkForUpdate");
    render(<App />);
    await screen.findByRole("button", { name: "Update available" });
    expect(look).not.toHaveBeenCalled();
  });
});

describe("the bar at the top", () => {
  const JOB = "DAVENPORT_2840 Brady Street - 2026 Tax";

  // Opened the way he opens it: from the Jobs screen.
  async function insideAJob() {
    quiet();
    api.listJobs.mockResolvedValue([{ name: JOB, photo_count: 12 }]);
    vi.spyOn(api, "jobDetail").mockResolvedValue({
      name: JOB, photo_count: 12, context: "", engagement: "", sections: [] });
    vi.spyOn(api, "jobFolders").mockResolvedValue({
      typical: [], other: [], root_files: [], missing_classifications: [] });
    vi.spyOn(api, "classificationLabels").mockResolvedValue({ labels: [] });
    vi.spyOn(api, "getSettings").mockResolvedValue({
      key_set: false, key_tail: "", workspace: "/jobs", demo_mode: false });
    render(<App />);
    await userEvent.click(await screen.findByText(JOB));
    await screen.findByRole("heading", { name: JOB });
  }

  // Spenser, 2026-09-04: "we need to make it obvious these are not computer
  // people." The job's own name is the crumb he needs most on the photos
  // screen, and it was plain white text that only underlined on hover.
  it("draws the way back to the job as a chip, the same as the way back to Jobs", async () => {
    await insideAJob();
    const crumb = screen.getByRole("button", { name: JOB });
    expect(crumb).toHaveClass("crumb-chip");
    expect(screen.getByRole("button", { name: /Back to Jobs/ })).toHaveClass("crumb-chip");
  });

  // Opening Settings threw the job away, so the only way back into it was
  // Jobs and then opening it again.
  it("keeps the job he was in when he opens Settings", async () => {
    await insideAJob();
    await userEvent.click(screen.getByRole("button", { name: "Settings" }));
    await screen.findByRole("heading", { name: "Settings" });
    await userEvent.click(screen.getByRole("button", { name: JOB }));
    await waitFor(() => expect(screen.getByRole("heading", { name: JOB })).toBeInTheDocument());
  });
});
