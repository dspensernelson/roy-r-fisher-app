/**
 * The band chips in the widget filter the photographs. Decided by Spenser on
 * 2026-09-17: click A and only band A's photographs show, click A again and
 * every photograph shows, click B and it switches to B.
 *
 * It is the screen only. Nothing is sent to the server, nothing is saved, the
 * report order never changes, and the counts keep counting the whole job.
 */
import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, afterEach } from "vitest";

import PhotosScreen from "./PhotosScreen.jsx";
import * as api from "../api.js";

const JOB = "ANYTOWN_100 Example Avenue - 2026";
const BANDS = [
  { letter: "A", name: "A", locked: true },
  { letter: "B", name: "B", locked: true },
  { letter: "C", name: "C", locked: true },
];

// Two in A, three in B, none in C, one waiting for a band.
const PHOTOS = [
  { file: "a1.jpg", caption: "Front", band: "A", reviewed: true, author: "ai" },
  { file: "a2.jpg", caption: "Side", band: "A", author: "ai" },
  { file: "b1.jpg", caption: "", band: "B" },
  { file: "b2.jpg", caption: "", band: "B" },
  { file: "b3.jpg", caption: "", band: "B" },
  { file: "none.jpg", caption: "" },
];

function manifest(over = {}) {
  return { job: JOB, context: "", report_year: 2026, caption_style: "view",
           photos: PHOTOS, bands_on: true, bands: BANDS, photos_per_page: 3,
           ...over };
}

function setUp(m = manifest()) {
  vi.spyOn(api, "getManifest").mockResolvedValue(m);
  vi.spyOn(api, "jobFacts").mockResolvedValue({
    ready: true, city: "Anytown", address: "100 Example Avenue",
    filename: "Anytown_100 Example Avenue Photos (Complete).docx", missing: [] });
  vi.spyOn(api, "captionEstimate").mockResolvedValue({
    photos_to_send: 4, tranches: 1, tranche_size: 60, needs_confirmation: false,
    estimate: { total: 0.2 }, ai_available: true, blocked_because: "" });
  vi.spyOn(api, "captionStyles").mockResolvedValue({ ai_available: true, styles: [] });
  vi.spyOn(api, "photoGroups").mockResolvedValue({
    groups: [{ folder: "", count: PHOTOS.length, sample: PHOTOS[0].file }],
    chosen: null, chosen_missing: false, needs_choice: false });
  vi.spyOn(api, "readingProgress").mockResolvedValue({ reading: false, done: 0, total: 0 });
  const saves = [
    vi.spyOn(api, "putManifest").mockResolvedValue({ ok: true }),
    vi.spyOn(api, "putBands").mockResolvedValue(m),
    vi.spyOn(api, "setPhotoBand").mockResolvedValue(m),
  ];
  render(<PhotosScreen job={JOB} onBack={() => {}} />);
  return saves;
}

afterEach(() => vi.restoreAllMocks());

const shown = () => Array.from(document.querySelectorAll(".grid figure img"))
  .map((img) => img.getAttribute("alt"));
const chip = (letter) => screen.getByRole("button", { name: `Band ${letter}` });
const ready = () => waitFor(() => expect(shown().length).toBe(PHOTOS.length));

describe("clicking a band chip", () => {
  it("shows every photograph until a chip is clicked", async () => {
    setUp();
    await ready();
    for (const l of ["A", "B", "C"]) expect(chip(l)).toHaveAttribute("aria-pressed", "false");
  });

  it("shows only that band's photographs", async () => {
    setUp();
    await ready();
    await userEvent.click(chip("B"));
    expect(shown()).toEqual(["b1.jpg", "b2.jpg", "b3.jpg"]);
  });

  it("shows every photograph again when the same chip is clicked", async () => {
    setUp();
    await ready();
    await userEvent.click(chip("A"));
    expect(shown()).toEqual(["a1.jpg", "a2.jpg"]);
    await userEvent.click(chip("A"));
    expect(shown()).toEqual(PHOTOS.map((p) => p.file));
  });

  it("switches straight to a different band", async () => {
    setUp();
    await ready();
    await userEvent.click(chip("A"));
    await userEvent.click(chip("B"));
    expect(shown()).toEqual(["b1.jpg", "b2.jpg", "b3.jpg"]);
  });

  it("marks the one chip that is filtering, and only that one", async () => {
    setUp();
    await ready();
    await userEvent.click(chip("B"));
    expect(chip("B")).toHaveAttribute("aria-pressed", "true");
    expect(chip("B")).toHaveClass("is-on");
    for (const l of ["A", "C"]) {
      expect(chip(l)).toHaveAttribute("aria-pressed", "false");
      expect(chip(l)).not.toHaveClass("is-on");
    }
  });
});

describe("what the filter never touches", () => {
  it("sends nothing to the server and saves nothing", async () => {
    const saves = setUp();
    await ready();
    await userEvent.click(chip("A"));
    await userEvent.click(chip("B"));
    await userEvent.click(chip("B"));
    for (const one of saves) expect(one).not.toHaveBeenCalled();
  });

  it("keeps counting the whole job, not what is showing", async () => {
    setUp();
    await ready();
    const figures = () => document.querySelector(".figures").textContent;
    const bar = () => document.querySelector(".control-panel .barline").textContent;
    const before = [figures(), bar()];
    await userEvent.click(chip("A"));
    expect(shown()).toHaveLength(2);
    expect([figures(), bar()]).toEqual(before);
    expect(figures()).toMatch(/6 photographs · 2 pages/);
    expect(bar()).toMatch(/1\sof\s2\sreviewed/);
  });
});

describe("a photograph moved while a filter is on", () => {
  it("leaves the view when it goes to another band", async () => {
    setUp();
    await ready();
    await userEvent.click(chip("A"));
    const moved = manifest({ photos: PHOTOS.map((p) =>
      (p.file === "a2.jpg" ? { ...p, band: "B" } : p)) });
    api.setPhotoBand.mockResolvedValue(moved);
    const a2 = document.querySelectorAll(".grid figure")[1];
    await userEvent.click(a2.querySelector('[aria-label="Put in band B"]'));
    await waitFor(() => expect(shown()).toEqual(["a1.jpg"]));
  });
});

describe("with bands switched off", () => {
  it("applies no filter", async () => {
    setUp();
    await ready();
    await userEvent.click(chip("A"));
    expect(shown()).toHaveLength(2);
    api.putBands.mockResolvedValue(manifest({ bands_on: false }));
    await userEvent.click(screen.getByRole("switch", { name: "Bands" }));
    await waitFor(() => expect(shown()).toEqual(PHOTOS.map((p) => p.file)));
  });

  it("does not come back filtered when bands are switched on again", async () => {
    setUp();
    await ready();
    await userEvent.click(chip("A"));
    api.putBands.mockResolvedValue(manifest({ bands_on: false }));
    await userEvent.click(screen.getByRole("switch", { name: "Bands" }));
    await waitFor(() => expect(shown()).toHaveLength(PHOTOS.length));
    api.putBands.mockResolvedValue(manifest());
    await userEvent.click(screen.getByRole("switch", { name: "Bands" }));
    await waitFor(() => expect(chip("A")).toHaveAttribute("aria-pressed", "false"));
    expect(shown()).toHaveLength(PHOTOS.length);
  });
});
