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

// Spenser, 2026-09-18: one pill, "N of M reviewed". Who wrote each caption is
// on the photograph, not in the bar.
const pillText = () => Array.from(bar().querySelectorAll(".pill"))
  .map((p) => p.textContent.replace(/ /g, " ").trim());

// Spenser, 2026-09-18, from 0.7.6.3 on his virtual machine. Three things
// were wrong with this one pill and each is held here:
//
// - M is every photograph in the report, captioned or not. It counted only
//   the captioned ones, so the pill went to done with 17 photographs that had
//   no words at all. docs/CHECKS.md, Check 40, already said M is the
//   photographs in the report.
// - The tick means one thing: everything is reviewed. The tick-all offer
//   wore it too, so "✓ 11 of 12 reviewed" read as done when it was not. The
//   offer is still the pill, but amber and with no tick, and its hover says
//   what the click does.
// - Done is the pale green tint with the light tick green, not a solid dark
//   green fill: "I don't like the dark green."
const HOVER = "Mark every caption as reviewed";
const offer = () => screen.queryByRole("button", { name: HOVER });

describe("the bar, and the one count", () => {
  it("counts reviewed out of every photograph in the report", async () => {
    setUp({ written: 5, reviewed: 0 });
    await waitFor(() => expect(bar()).toBeTruthy());
    expect(pillText()).toEqual(["0 of 12 reviewed"]);
  });

  it("is not done while photographs have no caption, however many are reviewed", async () => {
    // His screenshot: five written, five reviewed, seventeen with nothing.
    setUp({ written: 5, reviewed: 5, total: 22 });
    await waitFor(() => expect(bar()).toBeTruthy());
    expect(pillText()).toEqual(["5 of 22 reviewed"]);
    expect(bar().querySelector(".pill.done")).toBeNull();
    expect(bar().querySelector(".pill").className).toMatch(/\bhold\b/);
  });

  it("says nothing about who wrote them", async () => {
    setUp({ written: 5, reviewed: 1 });
    await waitFor(() => expect(bar()).toBeTruthy());
    expect(bar().textContent).not.toMatch(/\bAI\b|typed/);
  });

  it("carries no tick while one photograph is still to review", async () => {
    setUp({ written: 12, reviewed: 11 });
    const pill = await screen.findByRole("button", { name: HOVER });
    expect(pillText()).toEqual(["11 of 12 reviewed"]);
    expect(pill.textContent).not.toMatch(/✓/);
    // The amber the widget uses for what still needs him, not a green.
    expect(pill.className).toMatch(/\bhold\b/);
    expect(pill.className).not.toMatch(/\bdone\b/);
  });

  it("is still the offer to tick the lot, and says so when hovered", async () => {
    setUp({ written: 12, reviewed: 3 });
    const pill = await screen.findByRole("button", { name: HOVER });
    expect(pill).toHaveAttribute("title", HOVER);
    expect(bar().querySelectorAll(".pill")).toHaveLength(1);
    await userEvent.click(pill);
    expect(screen.getByRole("heading", { name: "Mark every caption as reviewed?" }))
      .toBeInTheDocument();
  });

  it("does not offer the tick-all while captions are still being written", async () => {
    setUp({ written: 5, reviewed: 0 });
    await waitFor(() => expect(bar()).toBeTruthy());
    expect(offer()).toBeNull();
    expect(pillText()).toEqual(["0 of 12 reviewed"]);
  });

  it("counts only the photographs still in the report", async () => {
    // Two taken out, both with captions, one of them reviewed. Neither counts.
    setUp({ written: 5, reviewed: 2, taken: [
      { caption: "Taken out, written", reviewed: true },
      { caption: "Taken out, also written" },
    ] });
    await waitFor(() => expect(bar()).toBeTruthy());
    expect(pillText()).toEqual(["2 of 12 reviewed"]);
  });

  it("is done with photographs taken out, when every one left is reviewed", async () => {
    setUp({ written: 3, reviewed: 3, total: 3, taken: [
      { caption: "Taken out" },
      { caption: "" },
    ] });
    await waitFor(() => expect(bar()).toBeTruthy());
    expect(pillText()).toEqual(["✓ 3 of 3 reviewed"]);
    expect(bar().querySelector(".pill.done")).toBeTruthy();
  });

  it("offers the tick-all when every photograph in the report is written", async () => {
    // A photograph taken out without a caption does not hold the offer back.
    setUp({ written: 12, reviewed: 3, taken: [{ caption: "" }] });
    expect(await screen.findByRole("button", { name: HOVER })).toBeInTheDocument();
  });

  it("says it is done, with the tick, once every one is reviewed", async () => {
    setUp({ written: 12, reviewed: 12 });
    await waitFor(() => expect(bar()).toBeTruthy());
    expect(pillText()).toEqual(["✓ 12 of 12 reviewed"]);
    expect(bar().querySelector(".pill.done")).toBeTruthy();
    expect(offer()).toBeNull();
  });

  it("is not done while two photographs are blank, even with the rest reviewed", async () => {
    setUp({ written: 10, reviewed: 10, total: 12 });
    await waitFor(() => expect(bar()).toBeTruthy());
    expect(pillText()).toEqual(["10 of 12 reviewed"]);
    expect(bar().querySelector(".pill.done")).toBeNull();
    expect(screen.getByRole("button", { name: "Build photo pages" })).toBeDisabled();
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
    expect(pillText()).toEqual(["0 of 12 reviewed"]);
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

// Spenser, 2026-09-18: "The caption button doesn't get smaller the more I
// review." Its count is the photographs with no caption, so reviewing does
// not move it, and it should not. Typing words into an empty one should, and
// in 0.7.6.3 it did not: the count was asked for only when the screen opened,
// after a run and when the spending window opened. Seen in the running app
// on 2026-09-18: two empty, one typed, the button still said (2).
//
// The count is the screen's own, counted from the photographs it holds. It
// is not asked of the server on each caption: the price is asked for when the
// screen opens and when the spending window opens (Spenser, 2026-09-14,
// after Colleen's screen stopped answering on the office network).
describe("the count on Generate captions", () => {
  const generate = () => screen.getByRole("button", { name: /^Generate captions/ });
  const boxes = () => document.querySelectorAll(".grid figure textarea");

  it("drops by one when he types a caption into an empty photograph", async () => {
    setUp({ written: 10, reviewed: 10, total: 12 });
    await waitFor(() => expect(generate()).toHaveTextContent("Generate captions (2)"));
    vi.spyOn(api, "putManifest").mockResolvedValue({ ok: true });
    const asked = api.captionEstimate.mock.calls.length;
    await userEvent.type(boxes()[10], "Side yard");
    await userEvent.tab();
    await waitFor(() => expect(generate()).toHaveTextContent("Generate captions (1)"));
    // and without asking the server for a price
    expect(api.captionEstimate.mock.calls.length).toBe(asked);
  });

  it("comes alive when he empties a caption on a job that had them all", async () => {
    setUp({ written: 12, reviewed: 12, total: 12 });
    await waitFor(() => expect(bar()).toBeTruthy());
    expect(generate()).toBeDisabled();
    vi.spyOn(api, "putManifest").mockResolvedValue({ ok: true });
    await userEvent.clear(boxes()[3]);
    await userEvent.tab();
    await waitFor(() => expect(generate()).toHaveTextContent("Generate captions (1)"));
    expect(generate()).toBeEnabled();
  });

  it("does not move when he only reviews", async () => {
    setUp({ written: 10, reviewed: 5, total: 12 });
    await waitFor(() => expect(generate()).toHaveTextContent("Generate captions (2)"));
    vi.spyOn(api, "markReviewed").mockResolvedValue({
      job: JOB, caption_style: "view", bands_on: true, bands: ["A", "B", "C"], report_year: 2026,
      photos: Array.from({ length: 12 }, (_, i) => photo(i, {
        caption: i < 10 ? `A caption ${i}` : "", reviewed: i < 6 })) });
    const tile = document.querySelectorAll(".grid figure")[5];
    await userEvent.click(tile.querySelector('[aria-label="Mark reviewed"]'));
    await waitFor(() => expect(pillText()).toEqual(["6 of 12 reviewed"]));
    expect(generate()).toHaveTextContent("Generate captions (2)");
  });

  it("counts every photograph after the captions are cleared", async () => {
    setUp({ written: 10, reviewed: 10, total: 12 });
    await waitFor(() => expect(generate()).toHaveTextContent("Generate captions (2)"));
    vi.spyOn(api, "clearCaptions").mockResolvedValue({
      job: JOB, caption_style: "view", bands_on: true, bands: ["A", "B", "C"], report_year: 2026,
      photos: Array.from({ length: 12 }, (_, i) => photo(i)), cleared: 10 });
    await userEvent.click(bar().querySelector(".clear"));
    await userEvent.click(await screen.findByRole("button", { name: "Clear 10 captions" }));
    await waitFor(() => expect(generate()).toHaveTextContent("Generate captions (12)"));
  });
});
