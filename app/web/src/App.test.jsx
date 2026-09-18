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
    vi.spyOn(api, "getSettings").mockResolvedValue({ key_set: false, ends_with: "" });
    render(<App />);
    const notice = await screen.findByRole("button", { name: "Update available" });
    expect(screen.queryByText(/Update to version 0\.5\.4\?/)).toBeNull();
    await userEvent.click(notice);
    expect(await screen.findByText(/Update to version 0\.5\.4\?/)).toBeInTheDocument();
    expect(screen.getByText(/about 53 MB/)).toBeInTheDocument();
  });

  it("closes again on Not now, and the notice stays", async () => {
    quiet({ available: "0.5.4", size: 55939858 });
    vi.spyOn(api, "getSettings").mockResolvedValue({ key_set: false, ends_with: "" });
    render(<App />);
    await userEvent.click(
      await screen.findByRole("button", { name: "Update available" }));
    await userEvent.click(await screen.findByRole("button", { name: "Not now" }));
    expect(screen.queryByText(/Update to version 0\.5\.4\?/)).toBeNull();
    expect(screen.getByRole("button", { name: "Update available" }))
      .toBeInTheDocument();
    // The card as it normally is, with Check now back in it.
    expect(screen.getByRole("button", { name: "Check now" })).toBeInTheDocument();
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

describe("the update button on Settings", () => {
  it("opens the same update step as the masthead", async () => {
    // Spenser, 2026-09-16: "When Check now finds a version, an Update button
    // appears beside it." One route into the update, not two.
    quiet();
    vi.spyOn(api, "getSettings").mockResolvedValue({ key_set: false, ends_with: "" });
    vi.spyOn(api, "checkForUpdate").mockResolvedValue({ available: "0.5.4" });
    render(<App />);
    await userEvent.click(await screen.findByRole("button", { name: "Settings" }));
    const check = await screen.findByRole("button", { name: "Check now" });

    // The server now remembers the newer version, as it does after a look.
    api.updateStatus.mockResolvedValue({
      version: "0.5.3", available: "0.5.4", size: 55939858, looked: true,
      run: { running: false, stage: "", done: 0, total: 0, error: "" },
    });
    await userEvent.click(check);

    const beside = await within(check.parentElement)
      .findByRole("button", { name: "Update available" });
    expect(screen.queryByText(/Update to version 0\.5\.4\?/)).toBeNull();
    await userEvent.click(beside);
    expect(within(versionCard()).getByText(/Update to version 0\.5\.4\?/)).toBeInTheDocument();
    expect(within(versionCard()).getByText(/about 53 MB/)).toBeInTheDocument();
  });
});

// Spenser, 2026-09-18, on 0.7.6.3: "I actually think the whole update should
// take place in the update box, not above the settings." One place: the card
// "The version you are running" on Settings. The masthead's button takes him
// there.
function versionCard() {
  return screen.getByRole("heading", { name: "The version you are running" })
    .closest(".setting");
}

function run(over = {}) {
  return { running: true, stage: "Downloading", done: 0, total: 55939858,
           error: "", version: "0.5.4", cancelling: false, ...over };
}

async function openFromTheMasthead() {
  quiet({ available: "0.5.4", size: 55939858 });
  vi.spyOn(api, "getSettings").mockResolvedValue({ key_set: false, ends_with: "" });
  render(<App />);
  await userEvent.click(await screen.findByRole("button", { name: "Update available" }));
  await screen.findByRole("heading", { name: "The version you are running" });
}

describe("the update happens inside the version card", () => {
  it("takes him from the masthead to Settings with the question in the card", async () => {
    await openFromTheMasthead();
    const card = versionCard();
    expect(within(card).getByText(/Update to version 0\.5\.4\?/)).toBeInTheDocument();
    expect(within(card).getByRole("button", { name: "Update now" })).toBeInTheDocument();
    expect(within(card).getByRole("button", { name: "Not now" })).toBeInTheDocument();
    // His words, 2026-09-17, kept exactly, less the version: the card's own
    // first line already says it (2026-09-18).
    const said = card.textContent.replace(/\s+/g, " ");
    expect(said).toContain(
      "The download is about 53 MB. The app closes " +
      "itself and opens again as a new version. Your settings remain the same.");
    expect(said).not.toMatch(/You are on version/);
    expect(said.match(/0\.5\.3/g)).toHaveLength(1);
    // Nothing drawn above the cards, and one of it.
    expect(document.querySelectorAll(".update-step")).toHaveLength(1);
    expect(card.contains(document.querySelector(".update-step"))).toBe(true);
  });

  it("shows the progress in the card", async () => {
    await openFromTheMasthead();
    vi.spyOn(api, "startUpdate").mockResolvedValue({});
    vi.spyOn(api, "updateProgress").mockResolvedValue(run({ done: 12 * 1024 * 1024 }));
    await userEvent.click(within(versionCard()).getByRole("button", { name: "Update now" }));
    await waitFor(() => expect(
      within(versionCard()).getByText("Downloading 12 MB of 53 MB")).toBeInTheDocument());
    expect(versionCard().querySelector(".update-bar")).not.toBeNull();
    expect(document.querySelectorAll(".update-bar")).toHaveLength(1);
  });

  it("shows a failed download in the card", async () => {
    await openFromTheMasthead();
    vi.spyOn(api, "startUpdate").mockResolvedValue({});
    vi.spyOn(api, "updateProgress").mockResolvedValue(run({
      running: false, stage: "",
      error: "The update did not arrive intact and was not installed." }));
    await userEvent.click(within(versionCard()).getByRole("button", { name: "Update now" }));
    await waitFor(() => expect(
      within(versionCard()).getByText(/did not arrive intact/)).toBeInTheDocument());
    await userEvent.click(within(versionCard()).getByRole("button", { name: "Close" }));
    expect(screen.queryByText(/did not arrive intact/)).toBeNull();
    expect(within(versionCard()).getByRole("button", { name: "Check now" })).toBeInTheDocument();
  });

  it("keeps running if he leaves Settings, and the closing cover still finds him", async () => {
    // The run belongs to the app, not to the card. Leaving Settings in the
    // middle of a download must not stop this tab becoming the new version.
    await openFromTheMasthead();
    vi.spyOn(api, "startUpdate").mockResolvedValue({});
    const progress = vi.spyOn(api, "updateProgress").mockResolvedValue(run());
    await userEvent.click(within(versionCard()).getByRole("button", { name: "Update now" }));
    await waitFor(() => within(versionCard()).getByText(/Downloading/));

    await userEvent.click(screen.getByRole("button", { name: /Back to Jobs/ }));
    expect(screen.queryByRole("heading", { name: "The version you are running" })).toBeNull();

    progress.mockResolvedValue(run({ running: false, stage: "Closing" }));
    await waitFor(() => expect(
      screen.getByText("Installing the new version.")).toBeInTheDocument(), { timeout: 3000 });
  });

  it("shows the run where it is when he comes back to Settings", async () => {
    await openFromTheMasthead();
    vi.spyOn(api, "startUpdate").mockResolvedValue({});
    vi.spyOn(api, "updateProgress").mockResolvedValue(run({ done: 12 * 1024 * 1024 }));
    await userEvent.click(within(versionCard()).getByRole("button", { name: "Update now" }));
    await waitFor(() => within(versionCard()).getByText("Downloading 12 MB of 53 MB"));
    await userEvent.click(screen.getByRole("button", { name: /Back to Jobs/ }));
    await userEvent.click(screen.getByRole("button", { name: "Settings" }));
    await waitFor(() => expect(
      within(versionCard()).getByText("Downloading 12 MB of 53 MB")).toBeInTheDocument());
  });

  it("does not keep an unanswered question waiting after he walks away", async () => {
    // North star 4: never an old screen. He opened the question and left
    // without answering; coming back, the card is as it normally is.
    await openFromTheMasthead();
    await userEvent.click(screen.getByRole("button", { name: /Back to Jobs/ }));
    await userEvent.click(screen.getByRole("button", { name: "Settings" }));
    await screen.findByRole("heading", { name: "The version you are running" });
    expect(screen.queryByText(/Update to version 0\.5\.4\?/)).toBeNull();
    expect(within(versionCard()).getByRole("button", { name: "Check now" })).toBeInTheDocument();
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

  // Spenser, 2026-09-15: "that is a weird place for that comment". Under the
  // question sat "Closing the browser tab does not stop it. This does.", which
  // explains why the button exists to somebody who has already pressed it.
  it("asks the question and says nothing else", async () => {
    await onJobs();
    await userEvent.click(screen.getByRole("button", { name: "Close the app" }));
    const asked = await screen.findByRole("dialog", { name: "Close the app?" });
    expect(asked.textContent).not.toMatch(/browser tab/i);
    expect(within(asked).getByRole("heading", { name: "Close the app?" })).toBeInTheDocument();
    expect(within(asked).getByRole("button", { name: "Cancel" })).toBeInTheDocument();
    expect(within(asked).getByRole("button", { name: "Close the app" })).toBeInTheDocument();
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
