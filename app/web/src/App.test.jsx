import React from "react";
import { render, screen, waitFor, within } from "@testing-library/react";
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

// F13, approved 2026-09-03 and built on 2026-09-15 to the mockup the owner
// corrected comment by comment. `Close the app` comes out of Settings and
// sits in the dark bar, so it is one click away from every screen.
describe("Close the app, in the nav bar", () => {
  const JOB = "DAVENPORT_2840 Brady Street - 2026 Tax";

  async function onJobs() {
    quiet();
    render(<App />);
    await screen.findByRole("button", { name: "Settings" });
  }

  it("sits in the bar as a solid red box, not a link", async () => {
    await onJobs();
    const box = screen.getByRole("button", { name: "Close the app" });
    expect(box).toHaveClass("bar-close");
    expect(box.closest(".bar-inner")).not.toBeNull();
  });

  it("asks in a window over whatever screen he is on", async () => {
    quiet();
    api.listJobs.mockResolvedValue([{ name: JOB, photo_count: 12 }]);
    vi.spyOn(api, "jobDetail").mockResolvedValue({
      name: JOB, photo_count: 12, context: "", engagement: "", sections: [] });
    vi.spyOn(api, "jobFolders").mockResolvedValue({
      typical: [], other: [], root_files: [], missing_classifications: [] });
    vi.spyOn(api, "classificationLabels").mockResolvedValue({ labels: [] });
    render(<App />);
    await userEvent.click(await screen.findByText(JOB));
    await screen.findByRole("heading", { name: JOB });

    await userEvent.click(screen.getByRole("button", { name: "Close the app" }));
    const asked = await screen.findByRole("dialog", { name: "Close the app?" });
    expect(asked.closest(".sheet-back")).not.toBeNull();
    // The screen he was on is still there behind it, because Cancel puts
    // him back in it.
    expect(screen.getByRole("heading", { name: JOB })).toBeInTheDocument();
  });

  it("does nothing on Cancel", async () => {
    const stop = vi.spyOn(api, "closeTheApp").mockResolvedValue({});
    await onJobs();
    await userEvent.click(screen.getByRole("button", { name: "Close the app" }));
    await screen.findByRole("dialog", { name: "Close the app?" });
    await userEvent.click(screen.getByRole("button", { name: "Cancel" }));
    await waitFor(() => expect(screen.queryByRole("dialog", { name: "Close the app?" })).toBeNull());
    expect(stop).not.toHaveBeenCalled();
  });

  // B10: the app said "Closing now", the server stopped, and the tab sat for
  // ever with that sentence on a job list that looked perfectly usable.
  it("drains the whole app once it has actually closed", async () => {
    const stop = vi.spyOn(api, "closeTheApp").mockResolvedValue({});
    await onJobs();
    await userEvent.click(screen.getByRole("button", { name: "Close the app" }));
    const asked = await screen.findByRole("dialog", { name: "Close the app?" });
    await userEvent.click(within(asked).getByRole("button", { name: "Close the app" }));

    expect(await screen.findByText("Closing now.")).toBeInTheDocument();
    await waitFor(() => expect(stop).toHaveBeenCalled());
    expect(document.querySelector(".shell.finished")).not.toBeNull();
    expect(document.querySelector(".shell.finished #alive")).not.toBeNull();
    // Including the red box itself.
    expect(screen.getByRole("button", { name: "Close the app" })).toBeDisabled();
    // Nothing to back out to, so there is nothing left to press.
    expect(screen.queryByRole("button", { name: "Cancel" })).toBeNull();
  });
});
