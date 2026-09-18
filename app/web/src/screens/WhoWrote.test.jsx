/**
 * Who wrote each caption, on the screen. Spenser, 2026-09-18: a caption he
 * types himself counts as reviewed. The server decides who wrote it and
 * whether it is ticked (app/server/photos.py, `record_typed_captions`); the
 * screen shows what it is told and never works either out itself.
 *
 * Who wrote it shows on the photograph, under its caption, not in the bar.
 * The bar counts only "N of M reviewed". Spenser, 2026-09-18.
 */
import React from "react";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, afterEach } from "vitest";

import PhotosScreen from "./PhotosScreen.jsx";
import * as api from "../api.js";

const JOB = "ANYTOWN_100 Example Avenue - 2026";

const PHOTOS = [
  { file: "a.jpg", caption: "View east", author: "ai", reviewed: true },
  { file: "b.jpg", caption: "Rear loading area", author: "ai" },
  { file: "c.jpg", caption: "Front entry, looking north", author: "person", reviewed: true },
  { file: "d.jpg", caption: "" },
  { file: "e.jpg", caption: "" },
];

function manifest(photos = PHOTOS) {
  return { job: JOB, context: "", report_year: 2026, caption_style: "view",
           photos, photos_per_page: 3 };
}

function setUp() {
  vi.spyOn(api, "getManifest").mockResolvedValue(manifest());
  vi.spyOn(api, "jobFacts").mockResolvedValue({
    ready: true, city: "Anytown", address: "100 Example Avenue",
    filename: "Anytown_100 Example Avenue Photos (Complete).docx", missing: [] });
  vi.spyOn(api, "captionEstimate").mockResolvedValue({
    photos_to_send: 1, tranches: 1, tranche_size: 60, needs_confirmation: false,
    estimate: { total: 0.05 }, ai_available: true, blocked_because: "" });
  vi.spyOn(api, "captionStyles").mockResolvedValue({ ai_available: true, styles: [] });
  vi.spyOn(api, "photoGroups").mockResolvedValue({
    groups: [{ folder: "", count: 5, sample: "a.jpg" }],
    chosen: null, chosen_missing: false, needs_choice: false });
  vi.spyOn(api, "readingProgress").mockResolvedValue({ reading: false, done: 0, total: 0 });
  render(<PhotosScreen job={JOB} onBack={() => {}} />);
}

afterEach(() => vi.restoreAllMocks());

const bar = () => document.querySelector(".control-panel .barline");
const tiles = () => Array.from(document.querySelectorAll(".grid figure"));
const tick = (tile) => tile.querySelector(".tick-dot");

const who = (tile) => tile.querySelector(".who");

describe("who wrote it, on the photograph", () => {
  it("marks an AI caption and a typed one under the caption", async () => {
    setUp();
    await waitFor(() => expect(tiles()).toHaveLength(5));
    expect(who(tiles()[0]).textContent).toBe("AI");
    expect(who(tiles()[1]).textContent).toBe("AI");
    expect(who(tiles()[2]).textContent).toBe("Typed");
  });

  it("says nothing when there is no caption, and keeps its place", async () => {
    setUp();
    await waitFor(() => expect(tiles()).toHaveLength(5));
    expect(who(tiles()[3])).toBeTruthy();
    expect(who(tiles()[3]).textContent).toBe("");
  });

  it("sits with the caption, not in the row of controls", async () => {
    setUp();
    await waitFor(() => expect(tiles()).toHaveLength(5));
    expect(who(tiles()[0]).closest(".review-line")).toBeNull();
    expect(who(tiles()[0]).tagName).not.toBe("BUTTON");
  });

  it("is not in the bar", async () => {
    setUp();
    await waitFor(() => expect(bar()).toBeTruthy());
    expect(bar().textContent).not.toMatch(/\bAI\b|typed/);
    expect(bar().textContent.replace(/\u00A0/g, " ")).toMatch(/2 of 5 reviewed/);
  });
});

describe("a caption he types", () => {
  it("is sent once, when he leaves the box, not on each key", async () => {
    setUp();
    await waitFor(() => expect(tiles()).toHaveLength(5));
    const put = vi.spyOn(api, "putManifest").mockResolvedValue({ ok: true });
    const box = within(tiles()[3]).getByRole("textbox");
    await userEvent.type(box, "Side yard");
    expect(put).not.toHaveBeenCalled();
    await userEvent.tab();
    await waitFor(() => expect(put).toHaveBeenCalledTimes(1));
  });

  it("shows the tick and his count the server answers with", async () => {
    setUp();
    await waitFor(() => expect(tiles()).toHaveLength(5));
    vi.spyOn(api, "putManifest").mockResolvedValue({ ok: true, manifest: manifest([
      ...PHOTOS.slice(0, 3),
      { file: "d.jpg", caption: "Side yard", author: "person", reviewed: true },
      PHOTOS[4],
    ]) });
    const box = within(tiles()[3]).getByRole("textbox");
    await userEvent.type(box, "Side yard");
    await userEvent.tab();
    await waitFor(() => expect(tick(tiles()[3])).toHaveClass("is-reviewed"));
    expect(who(tiles()[3]).textContent).toBe("Typed");
    expect(bar().textContent.replace(/\u00A0/g, " ")).toMatch(/3 of 5 reviewed/);
  });

  it("does not tick an AI caption on its own", async () => {
    setUp();
    await waitFor(() => expect(tiles()).toHaveLength(5));
    expect(tick(tiles()[1])).not.toHaveClass("is-reviewed");
  });
});
