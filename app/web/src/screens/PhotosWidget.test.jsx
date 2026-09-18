/**
 * The widget in the photographs screen's header, as Spenser approved it on
 * 2026-09-16 after moving every piece himself. The design is
 * `docs/design/photos-widget.html` and it wins over any judgement here.
 *
 * Each of these was got wrong at least once while he was watching, which is
 * why each is a test rather than a comment.
 */
import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import * as api from "../api.js";
import PhotosScreen from "./PhotosScreen.jsx";

const JOB = "A JOB";

// Every caption the server sends carries who wrote it (`author_of` in
// app/server/photos.py fills it in), so these do too. Written by the AI unless
// a test says otherwise.
function photo(n, { caption = "", reviewed = false, author } = {}) {
  const who = caption.trim() ? { author: author || "ai" } : {};
  return { file: `IMG_${n}.jpeg`, caption, reviewed, ...who };
}

function setUp({ written = 0, reviewed = 0, total = 12, taken = [] } = {}) {
  const photos = [];
  for (let i = 0; i < total; i += 1) {
    photos.push(photo(i, {
      caption: i < written ? `A caption ${i}` : "",
      reviewed: i < reviewed,
    }));
  }
  // Photographs taken out of the report. They keep their captions and their
  // place in the list, which is exactly what a real cut does.
  taken.forEach((one, n) => {
    photos.push({ ...photo(total + n, one), cut: true });
  });
  vi.spyOn(api, "getManifest").mockResolvedValue({
    job: JOB, photos, caption_style: "view", bands_on: true, bands: ["A", "B", "C"],
    per_page: 6, report_year: 2026,
  });
  vi.spyOn(api, "captionEstimate").mockResolvedValue({
    photos_to_send: total - written, tranche_size: 60, tranches: 1,
    needs_confirmation: false, blocked_because: "",
    estimate: { total: 0.06 },
  });
  vi.spyOn(api, "captionStyles").mockResolvedValue({ styles: [], ai_available: true });
  vi.spyOn(api, "photoGroups").mockResolvedValue({ chosen: "Originals", groups: [] });
  vi.spyOn(api, "readingProgress").mockResolvedValue({ running: false });
  vi.spyOn(api, "jobFacts").mockResolvedValue({ ready: true, city: "X", address: "Y" });
  render(<PhotosScreen job={JOB} onBack={() => {}} />);
}

afterEach(() => vi.restoreAllMocks());

const widget = () => document.querySelector(".control-panel");
const bar = () => document.querySelector(".control-panel .barline");

describe("the bar, and the two counts", () => {
  it("counts captions as they are written", async () => {
    setUp({ written: 5, reviewed: 0 });
    await waitFor(() => expect(bar()).toBeTruthy());
    expect(bar().textContent).toMatch(/5\s*AI/);
  });

  it("counts reviewed separately from written", async () => {
    setUp({ written: 12, reviewed: 3 });
    await waitFor(() => expect(bar()).toBeTruthy());
    // Not "3 written". The two numbers are different facts and this screen
    // showed one while claiming the other on 2026-09-16.
    expect(bar().textContent).toMatch(/3\s*reviewed/);
  });

  it("offers the check once every caption is written, as a glyph", async () => {
    setUp({ written: 12, reviewed: 3 });
    const tick = await screen.findByRole("button", { name: /mark every caption as reviewed/i });
    // The glyph, never the words. Overwritten twice on 2026-09-16.
    expect(tick.textContent.replace(/\s/g, "")).toBe("✓all");
    expect(tick.className).toMatch(/\bact\b/);
  });

  it("does not offer the check while captions are still being written", async () => {
    setUp({ written: 5, reviewed: 0 });
    await waitFor(() => expect(bar()).toBeTruthy());
    expect(screen.queryByRole("button", { name: /mark every caption as reviewed/i })).toBeNull();
    expect(bar().textContent).toMatch(/5\s*AI/);
  });

  it("counts written only among the photographs still in the report", async () => {
    // Every other count on the screen counts only what is still in. Written
    // counted every caption, so it could say more was written than the report
    // holds. Two taken out, both with captions, one of them reviewed.
    setUp({ written: 5, reviewed: 2, taken: [
      { caption: "Taken out, written", reviewed: true },
      { caption: "Taken out, also written" },
    ] });
    await waitFor(() => expect(bar()).toBeTruthy());
    expect(bar().textContent).toMatch(/(?<!\d)5\s*AI/);
    expect(bar().textContent).toMatch(/(?<!\d)2\s*reviewed/);
  });

  it("never shows more reviewed than written, with photographs taken out", async () => {
    // docs/NOW.md: reviewed can never be more than written, read from one
    // place. Both now read the photographs still in the report.
    setUp({ written: 3, reviewed: 3, taken: [
      { caption: "Taken out", reviewed: true },
      { caption: "Taken out", reviewed: true },
    ] });
    await waitFor(() => expect(bar()).toBeTruthy());
    const count = (word) => Number(bar().textContent.match(new RegExp(`(\\d+)\\s*${word}`))[1]);
    expect(count("AI") + count("typed")).toBe(3);
    expect(count("reviewed")).toBeLessThanOrEqual(count("AI") + count("typed"));
  });

  it("offers the check when every photograph in the report is written", async () => {
    // A photograph taken out without a caption does not hold the check back.
    setUp({ written: 12, reviewed: 3, taken: [{ caption: "" }] });
    expect(await screen.findByRole("button", { name: /mark every caption as reviewed/i }))
      .toBeInTheDocument();
  });

  it("says it is done, and stops offering, once everything is reviewed", async () => {
    setUp({ written: 12, reviewed: 12 });
    await waitFor(() => expect(bar()).toBeTruthy());
    expect(bar().textContent).toMatch(/All reviewed/);
    expect(screen.queryByRole("button", { name: /mark every caption as reviewed/i })).toBeNull();
    // and it does not also claim a count beside it
    expect(bar().textContent).not.toMatch(/AI|typed/);
  });
});

describe("what only appears when it is true", () => {
  it("has no Clear captions until there is a caption to lose", async () => {
    setUp({ written: 0 });
    await waitFor(() => expect(bar()).toBeTruthy());
    expect(bar().querySelector(".clear")).toBeNull();
  });

  it("shows Clear captions in red once there is one", async () => {
    setUp({ written: 1 });
    await waitFor(() => expect(bar().querySelector(".clear")).toBeTruthy());
    expect(bar().querySelector(".clear").textContent).toMatch(/Clear captions/);
  });

  it("still offers to clear, and quotes, every caption the server will clear", async () => {
    // Clearing blanks every caption in the job, including those on
    // photographs taken out. The confirmation quotes what the server acts on,
    // so it keeps counting those too, even though the written pill does not.
    setUp({ written: 0, taken: [{ caption: "Taken out, written" }] });
    await waitFor(() => expect(bar().querySelector(".clear")).toBeTruthy());
    expect(bar().textContent).toMatch(/(?<!\d)0\s*AI\s*0\s*typed/);
    await userEvent.click(bar().querySelector(".clear"));
    expect(screen.getByRole("heading", { name: "Clear 1 caption?" })).toBeInTheDocument();
  });

  it("shows the price before anything is generated, as an estimate", async () => {
    // The one moment she most wants to know what it will cost, and the moment
    // it used to be hidden.
    setUp({ written: 0 });
    await waitFor(() => expect(bar().querySelector(".money")).toBeTruthy());
    expect(bar().querySelector(".money").textContent).toMatch(/^~/);
  });

  it("drops the tilde once the money has actually been spent", async () => {
    setUp({ written: 12, reviewed: 0 });
    await waitFor(() => expect(bar().querySelector(".money")).toBeTruthy());
    expect(bar().querySelector(".money").textContent).not.toMatch(/^~/);
  });
});

describe("what the box is shaped like", () => {
  it("puts the photo button on the second row, under Build photo pages", async () => {
    setUp({ written: 3 });
    await waitFor(() => expect(widget()).toBeTruthy());
    const rows = widget().querySelectorAll(".w-row");
    expect(rows[1].querySelector(".w-icon")).toBeTruthy();
    expect(rows[0].querySelector(".w-icon")).toBeNull();
    // and Build is the first thing in the top row, so the button lands under it
    expect(rows[0].firstElementChild.textContent).toMatch(/Build photo pages/);
  });

  it("adds photos with an icon, not the words", async () => {
    setUp({ written: 3 });
    const add = await screen.findByRole("button", { name: /add photos/i });
    expect(add.className).toMatch(/w-icon/);
    expect(add.textContent.trim()).toBe("");
    expect(add.querySelector("svg")).toBeTruthy();
  });
});

describe("the left hand side", () => {
  it("no longer carries the reviewed note, because it moved into the box", async () => {
    setUp({ written: 12, reviewed: 9 });
    await waitFor(() => expect(bar()).toBeTruthy());
    const quiet = document.querySelector(".quiet");
    expect(quiet.textContent).not.toMatch(/9 of 12 reviewed/);
    expect(quiet.querySelector("button")?.textContent || "").not.toMatch(/Mark all as reviewed/);
  });
});
