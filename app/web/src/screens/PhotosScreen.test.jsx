import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";

import PhotosScreen from "./PhotosScreen.jsx";
import * as api from "../api.js";

const JOB = "ANYTOWN_100 Example Avenue - 2026";

function photos(n, caption = "") {
  return Array.from({ length: n }, (_, i) => ({
    file: `photo-${String(i + 1).padStart(2, "0")}.jpg`,
    caption, ...(caption ? { reviewed: true } : {}),
  }));
}

function manifest(over = {}) {
  return { job: JOB, context: "", report_year: 2026, caption_style: "view",
           photos: photos(3), ...over };
}

function estimate(over = {}) {
  return {
    photos_to_send: 3, tranches: 1, tranche_size: 60,
    needs_confirmation: false, confirm_above: 30,
    estimate: { label: "Estimated maximum cost", photos: 3, rate: 0.05,
                total: 0.15, arithmetic: "3 x $0.0500 = $0.15", is_estimate: true },
    ai_available: true, policy: "not_demo", may_send: true,
    blocked_because: "", ...over,
  };
}

const STYLES = {
  ai_available: true,
  styles: [
    { key: "view", label: "View of", sample: "View of x",
      samples: ["View of the front entrance", "View of the main office"],
      note: "", thin_evidence: false },
    { key: "category", label: "Location first", sample: "Building exterior – x",
      samples: ["Building exterior – front entrance", "Common area – main office"],
      note: "", thin_evidence: true },
  ],
};

beforeEach(() => {
  vi.spyOn(api, "getManifest").mockResolvedValue(manifest());
  vi.spyOn(api, "jobFacts").mockResolvedValue({
    ready: true, city: "Anytown", address: "100 Example Avenue",
    filename: "Anytown_100 Example Avenue Photos (Complete).docx", missing: [] });
  vi.spyOn(api, "captionEstimate").mockResolvedValue(estimate());
  vi.spyOn(api, "captionStyles").mockResolvedValue(STYLES);
  vi.spyOn(api, "putManifest").mockResolvedValue({ ok: true });
});

async function show() {
  render(<PhotosScreen job={JOB} />);
  await screen.findByRole("heading", { name: "Photos" });
}

describe("with no key on this computer", () => {
  beforeEach(() => {
    api.captionStyles.mockResolvedValue({ ...STYLES, ai_available: false });
    api.captionEstimate.mockResolvedValue(estimate({ blocked_because: "no_key",
                                                     ai_available: false }));
  });

  it("says so once, not twice", async () => {
    await show();
    await waitFor(() =>
      expect(screen.getAllByText(/needs a key on this computer/)).toHaveLength(1));
  });

  it("leaves generating off, and still allows typing a caption", async () => {
    await show();
    await waitFor(() =>
      expect(screen.getByRole("button", { name: /Generate captions/ })).toBeDisabled());
    expect(screen.getAllByPlaceholderText("Caption...")).toHaveLength(3);
  });
});

describe("choosing a style", () => {
  it("shows static examples and calls nobody", async () => {
    await show();
    await userEvent.click(await screen.findByRole("button", { name: /Generate captions/ }));
    expect(await screen.findByText("View of the front entrance")).toBeInTheDocument();
    // the only calls made are the ones the screen loads with
    expect(api.getManifest).toHaveBeenCalledTimes(1);
    expect(api.captionStyles).toHaveBeenCalledTimes(1);
  });

  it("switches the examples without asking the server again", async () => {
    await show();
    await userEvent.click(await screen.findByRole("button", { name: /Generate captions/ }));
    const before = api.captionStyles.mock.calls.length;
    await userEvent.click(screen.getByRole("button", { name: /Location first/ }));
    expect(await screen.findByText("Building exterior – front entrance")).toBeInTheDocument();
    expect(api.captionStyles.mock.calls.length).toBe(before);
  });
});

describe("above thirty photographs", () => {
  beforeEach(() => {
    api.getManifest.mockResolvedValue(manifest({ photos: photos(61) }));
    api.captionEstimate.mockResolvedValue(estimate({
      photos_to_send: 61, tranches: 2, needs_confirmation: true,
      estimate: { label: "Estimated maximum cost", photos: 61, rate: 0.05,
                  total: 3.05, arithmetic: "61 x $0.0500 = $3.05", is_estimate: true },
    }));
  });

  it("asks before anything is sent, and cancelling sends nothing", async () => {
    vi.spyOn(api, "draftCaptions").mockResolvedValue({});
    await show();
    await userEvent.click(await screen.findByRole("button", { name: /Generate captions/ }));
    await userEvent.click(await screen.findByRole("button", { name: "Use this style" }));

    expect(await screen.findByText(/Generate captions for 61 photos\?/)).toBeInTheDocument();
    // Twice on purpose: the figure, and the warning that repeats it.
    expect(screen.getAllByText("$3.05").length).toBeGreaterThanOrEqual(1);

    await userEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(api.draftCaptions).not.toHaveBeenCalled();
  });
});

describe("a run that saved some captions and not others", () => {
  beforeEach(() => {
    vi.spyOn(api, "draftCaptions").mockResolvedValue({
      ...manifest({ photos: photos(3, "View of something") }),
      ai_available: true, state: "partial", captioned: 2, remaining: ["photo-03.jpg"],
      summary: "2 captions were saved. 1 photo still needs a caption. The captions "
             + "already saved will not be sent or charged for again.",
      error: "Anthropic is busy or the account has hit a limit. Try again in a minute.",
      measured: { label: "Calculated API cost from measured usage",
                  tokens: { input: 1000, output: 200, cache_read: 0 },
                  calculated_cost: 0.02, note: "This app's arithmetic." },
    });
    vi.spyOn(api, "captionProgress").mockResolvedValue({ running: false });
  });

  async function runIt() {
    await show();
    await userEvent.click(await screen.findByRole("button", { name: /Generate captions/ }));
    await userEvent.click(await screen.findByRole("button", { name: "Use this style" }));
  }

  it("says what was saved and what is left, and never says nothing changed", async () => {
    await runIt();
    const said = await screen.findByText(/2 captions were saved\./);
    expect(said).toBeInTheDocument();
    expect(screen.queryByText(/Nothing was changed/)).toBeNull();
  });

  it("is a warning, not a success and not a failure", async () => {
    await runIt();
    const said = await screen.findByText(/2 captions were saved\./);
    expect(said.closest(".outcome")).toHaveClass("outcome-partial");
  });

  it("offers to retry only what is left", async () => {
    await runIt();
    expect(await screen.findByRole("button", { name: /Retry remaining 1 photo/ }))
      .toBeInTheDocument();
  });
});

describe("after a build", () => {
  beforeEach(() => {
    api.getManifest.mockResolvedValue(manifest({ photos: photos(3, "View of something") }));
    vi.spyOn(api, "build").mockResolvedValue({
      created: "Anytown_100 Example Avenue Photos (Complete).docx",
      folder: "/Users/mark/RRF Jobs/ANYTOWN_100 Example Avenue - 2026/Photos" });
    vi.spyOn(api, "reveal").mockResolvedValue({ opened: "x", folder: "y" });
    api.captionEstimate.mockResolvedValue(estimate({
      photos_to_send: 0, blocked_because: "nothing_to_do" }));
  });

  it("offers to open the document, and opens nothing on its own", async () => {
    await show();
    await userEvent.click(await screen.findByRole("button", { name: "Build photo pages" }));
    expect(await screen.findByRole("button", { name: "Open document" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Show in folder" })).toBeInTheDocument();
    expect(api.reveal).not.toHaveBeenCalled();
  });

  it("opens the exact file that was just built", async () => {
    await show();
    await userEvent.click(await screen.findByRole("button", { name: "Build photo pages" }));
    await userEvent.click(await screen.findByRole("button", { name: "Open document" }));
    expect(api.reveal).toHaveBeenCalledWith(
      JOB, "Anytown_100 Example Avenue Photos (Complete).docx", "document");
  });

  it("stops promising where it will go once it has gone there", async () => {
    await show();
    expect(screen.getByText(/Will be saved as/)).toBeInTheDocument();
    await userEvent.click(await screen.findByRole("button", { name: "Build photo pages" }));
    await screen.findByRole("button", { name: "Open document" });
    expect(screen.queryByText(/Will be saved as/)).toBeNull();
  });
});

describe("build is gated on review", () => {
  it("is off until every caption has been read", async () => {
    await show();
    expect(await screen.findByText(/0 of 3 reviewed/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Build photo pages" })).toBeDisabled();
  });

  it("comes alive when they all have", async () => {
    api.getManifest.mockResolvedValue(manifest({ photos: photos(3, "View of something") }));
    await show();
    expect(await screen.findByText(/3 of 3 reviewed\. Ready to build\./)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Build photo pages" })).toBeEnabled();
  });
});
