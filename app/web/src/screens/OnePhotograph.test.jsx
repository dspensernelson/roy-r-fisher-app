/**
 * Back and refresh, on one photograph, and the job-wide back in the widget's
 * bar. Spenser approved all three on 2026-09-17 from a drawing called
 * `one-photograph.html`. It is not in this repository yet and it wins over
 * any judgement here.
 *
 * Two of his decisions are what these mostly prove, because they are the two
 * that are easy to get quietly wrong:
 *
 * - The job-wide back SPARES what he changed. Anything typed or written again
 *   after the clear is left alone, which is what makes it safe to press twice.
 * - A caption put back NEVER brings its tick with it. It is read again, every
 *   time.
 */
import React from "react";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, afterEach } from "vitest";

import PhotosScreen from "./PhotosScreen.jsx";
import * as api from "../api.js";

const JOB = "ANYTOWN_100 Example Avenue - 2026";

function manifest(photos, over = {}) {
  return { job: JOB, context: "", report_year: 2026, caption_style: "view",
           photos, ...over };
}

function estimate(over = {}) {
  return {
    photos_to_send: 0, tranches: 1, tranche_size: 60,
    needs_confirmation: false, confirm_above: 30,
    estimate: { total: 0.15 },
    // What one photograph quotes as. Read off this one answer, once, for
    // every tile on the screen.
    one_photo: { label: "Estimated maximum cost", photos: 1, rate: 0.05,
                 total: 0.05, arithmetic: "1 x $0.0500 = $0.05",
                 is_estimate: true },
    ai_available: true, policy: "not_demo", may_send: true,
    blocked_because: "", samples: { photos: 0, styles: 2, estimate: { total: 0 } },
    ...over,
  };
}

function setUp(photos, { quote = {} } = {}) {
  vi.spyOn(api, "getManifest").mockResolvedValue(manifest(photos));
  vi.spyOn(api, "jobFacts").mockResolvedValue({
    ready: true, city: "Anytown", address: "100 Example Avenue",
    filename: "Anytown_100 Example Avenue Photos (Complete).docx", missing: [] });
  vi.spyOn(api, "captionEstimate").mockResolvedValue(estimate(quote));
  vi.spyOn(api, "captionStyles").mockResolvedValue({ ai_available: true, styles: [] });
  vi.spyOn(api, "putManifest").mockResolvedValue({ ok: true });
  vi.spyOn(api, "photoGroups").mockResolvedValue({
    groups: [{ folder: "", count: photos.length, sample: photos[0].file }],
    chosen: null, chosen_missing: false, needs_choice: false });
  vi.spyOn(api, "readingProgress").mockResolvedValue({ reading: false, done: 0, total: 0 });
  render(<PhotosScreen job={JOB} onBack={() => {}} />);
}

afterEach(() => vi.restoreAllMocks());

const tiles = () => Array.from(document.querySelectorAll(".grid figure"));
const bar = () => document.querySelector(".control-panel .barline");
const barBack = () => bar().querySelector(".bar-back");
const backOn = (tile) => tile.querySelector(".back-dot");
const refreshOn = (tile) => tile.querySelector(".refresh-dot");
const tickOn = (tile) => tile.querySelector(".tick-dot");

const WRITTEN = [
  { file: "photo-01.jpg", caption: "View east from Brady Street", reviewed: true },
  { file: "photo-02.jpg", caption: "Rear loading area" },
];
const CLEARED = [
  { file: "photo-01.jpg", caption: "", cleared_caption: "View east from Brady Street" },
  { file: "photo-02.jpg", caption: "", cleared_caption: "Rear loading area" },
];

describe("back, on one photograph", () => {
  it("is grey while nothing has been cleared for it", async () => {
    setUp(WRITTEN);
    await waitFor(() => expect(tiles().length).toBe(2));
    expect(backOn(tiles()[0]).disabled).toBe(true);

    // Grey says nothing. Spenser, 2026-09-17: "I don't think you need to say
    // anything in the grey. If it's great, it's great." No hover text; the
    // screen-reader name stays, so it is never a nameless button.
    expect(backOn(tiles()[0]).hasAttribute("title")).toBe(false);
    expect(backOn(tiles()[0]).getAttribute("aria-label")).toBe("Put the old caption back");
  });

  it("goes live on the tile whose caption was cleared", async () => {
    setUp(CLEARED);
    await waitFor(() => expect(tiles().length).toBe(2));
    expect(backOn(tiles()[0]).disabled).toBe(false);
    expect(backOn(tiles()[0]).getAttribute("title")).toBe("Put the old caption back");
  });

  it("is live on one tile and grey on another, independently", async () => {
    setUp([CLEARED[0], WRITTEN[1]]);
    await waitFor(() => expect(tiles().length).toBe(2));
    expect(backOn(tiles()[0]).disabled).toBe(false);
    expect(backOn(tiles()[1]).disabled).toBe(true);
  });

  it("asks the server for that one photograph and draws what comes back", async () => {
    setUp(CLEARED);
    const back = vi.spyOn(api, "captionBack").mockResolvedValue(manifest([
      { file: "photo-01.jpg", caption: "View east from Brady Street",
        cleared_caption: "View east from Brady Street" },
      CLEARED[1],
    ]));
    await waitFor(() => expect(tiles().length).toBe(2));

    await userEvent.click(backOn(tiles()[0]));

    expect(back).toHaveBeenCalledWith(JOB, "photo-01.jpg");
    await waitFor(() => expect(
      within(tiles()[0]).getByRole("textbox").value).toBe("View east from Brady Street"));
    // The other one is untouched.
    expect(within(tiles()[1]).getByRole("textbox").value).toBe("");
  });

  it("puts the caption back without its tick", async () => {
    // Ticked before the clear. It comes back unticked, because it has been
    // off the screen since and has to be read again.
    setUp(CLEARED);
    vi.spyOn(api, "captionBack").mockResolvedValue(manifest([
      { file: "photo-01.jpg", caption: "View east from Brady Street",
        cleared_caption: "View east from Brady Street" },
      CLEARED[1],
    ]));
    await waitFor(() => expect(tiles().length).toBe(2));

    await userEvent.click(backOn(tiles()[0]));

    await waitFor(() => expect(
      within(tiles()[0]).getByRole("textbox").value).toBe("View east from Brady Street"));
    expect(tickOn(tiles()[0]).className).not.toMatch(/is-reviewed/);
    expect(tickOn(tiles()[0]).getAttribute("aria-label")).toBe("Mark reviewed");
  });

  it("does not need the job-wide one to have been pressed", async () => {
    setUp(CLEARED);
    const all = vi.spyOn(api, "captionsBack").mockResolvedValue(manifest(CLEARED));
    vi.spyOn(api, "captionBack").mockResolvedValue(manifest(CLEARED));
    await waitFor(() => expect(tiles().length).toBe(2));

    await userEvent.click(backOn(tiles()[0]));

    expect(all).not.toHaveBeenCalled();
  });
});

describe("refresh, on one photograph", () => {
  it("carries the price of one photograph inside it", async () => {
    setUp(WRITTEN);
    await waitFor(() => expect(tiles().length).toBe(2));
    expect(refreshOn(tiles()[0]).textContent).toContain("~5¢");
    expect(refreshOn(tiles()[0]).getAttribute("title"))
      .toBe("Write a new caption, ~5¢");
  });

  it("reads that price once for the whole screen, not once per tile", async () => {
    // The fault this guards against is recorded: the screen asked the server
    // for the caption price on every keystroke, one trip across the office
    // network per letter. A figure printed on sixty tiles must not become
    // sixty questions either.
    const many = Array.from({ length: 12 }, (_, i) => (
      { file: `photo-${i}.jpg`, caption: `A caption ${i}` }));
    setUp(many);
    await waitFor(() => expect(tiles().length).toBe(12));
    expect(api.captionEstimate).toHaveBeenCalledTimes(1);
  });

  it("says nothing about a price it has not been told", async () => {
    setUp(WRITTEN, { quote: { one_photo: undefined } });
    await waitFor(() => expect(tiles().length).toBe(2));
    expect(refreshOn(tiles()[0]).textContent).not.toContain("¢");
    expect(refreshOn(tiles()[0]).getAttribute("title")).toBe("Write a new caption");
  });

  it("asks the server for one photograph and draws what comes back", async () => {
    setUp(WRITTEN);
    const again = vi.spyOn(api, "refreshCaption").mockResolvedValue(manifest([
      { file: "photo-01.jpg", caption: "A different set of words" },
      WRITTEN[1],
    ]));
    await waitFor(() => expect(tiles().length).toBe(2));

    await userEvent.click(refreshOn(tiles()[0]));

    expect(again).toHaveBeenCalledWith(JOB, "photo-01.jpg");
    await waitFor(() => expect(
      within(tiles()[0]).getByRole("textbox").value).toBe("A different set of words"));
  });

  it("leaves the new caption unticked", async () => {
    setUp(WRITTEN);
    vi.spyOn(api, "refreshCaption").mockResolvedValue(manifest([
      { file: "photo-01.jpg", caption: "A different set of words" },
      WRITTEN[1],
    ]));
    await waitFor(() => expect(tiles().length).toBe(2));
    expect(tickOn(tiles()[0]).className).toMatch(/is-reviewed/);

    await userEvent.click(refreshOn(tiles()[0]));

    await waitFor(() => expect(
      tickOn(tiles()[0]).className).not.toMatch(/is-reviewed/));
  });

  it("leaves Back live, and Back puts the replaced words back", async () => {
    // Spenser, 2026-09-18: Back undoes a Refresh. The server keeps the words
    // Refresh replaced as the photograph's spare, the way a clear does.
    setUp(WRITTEN);
    vi.spyOn(api, "refreshCaption").mockResolvedValue(manifest([
      { file: "photo-01.jpg", caption: "A different set of words",
        cleared_caption: "View east from Brady Street" },
      WRITTEN[1],
    ]));
    const back = vi.spyOn(api, "captionBack").mockResolvedValue(manifest([
      { file: "photo-01.jpg", caption: "View east from Brady Street",
        cleared_caption: "View east from Brady Street" },
      WRITTEN[1],
    ]));
    await waitFor(() => expect(tiles().length).toBe(2));
    expect(backOn(tiles()[0]).disabled).toBe(true);

    await userEvent.click(refreshOn(tiles()[0]));
    await waitFor(() => expect(backOn(tiles()[0]).disabled).toBe(false));
    // The job-wide back is for what a clear emptied. Nothing is empty here.
    expect(barBack().disabled).toBe(true);

    await userEvent.click(backOn(tiles()[0]));
    expect(back).toHaveBeenCalledWith(JOB, "photo-01.jpg");
    await waitFor(() => expect(
      within(tiles()[0]).getByRole("textbox").value).toBe("View east from Brady Street"));
    // Put back without its tick: it was ticked before the refresh.
    expect(tickOn(tiles()[0]).className).not.toMatch(/is-reviewed/);
  });

  it("is grey when there is no key on this computer", async () => {
    setUp(WRITTEN, { quote: { blocked_because: "no_key", ai_available: false } });
    await waitFor(() => expect(tiles().length).toBe(2));
    expect(refreshOn(tiles()[0]).disabled).toBe(true);
  });

  it("is grey when these photographs may not leave the machine", async () => {
    setUp(WRITTEN, { quote: { blocked_because: "local_only" } });
    await waitFor(() => expect(tiles().length).toBe(2));
    expect(refreshOn(tiles()[0]).disabled).toBe(true);
  });

  it("stays live when every caption is already written", async () => {
    // `nothing_to_do` stops a whole-job run and must not stop this one: a
    // caption he does not like is exactly what refresh is for.
    setUp(WRITTEN, { quote: { blocked_because: "nothing_to_do" } });
    await waitFor(() => expect(tiles().length).toBe(2));
    expect(refreshOn(tiles()[0]).disabled).toBe(false);
  });
});

describe("the job-wide back, in the bar", () => {
  it("is grey until a clear has happened", async () => {
    setUp(WRITTEN);
    await waitFor(() => expect(bar()).toBeTruthy());
    expect(barBack().disabled).toBe(true);

    // Grey says nothing. Spenser, 2026-09-17: "I don't think you need to say
    // anything in the grey. If it's great, it's great." No hover text; the
    // screen-reader name stays, so it is never a nameless button.
    expect(barBack().hasAttribute("title")).toBe(false);
    expect(barBack().getAttribute("aria-label")).toBe("Restore cleared captions");
  });

  it("goes live once captions have been cleared", async () => {
    setUp(CLEARED);
    await waitFor(() => expect(bar()).toBeTruthy());
    expect(barBack().disabled).toBe(false);
  });

  it("says Spenser's words when it is live, and only those", async () => {
    // Spenser's wording, exactly, 2026-09-18. It replaced "Put every caption
    // back" in both the hover text and what a screen reader hears.
    setUp(CLEARED);
    await waitFor(() => expect(bar()).toBeTruthy());
    expect(barBack().getAttribute("title")).toBe("Restore cleared captions");
    expect(barBack().getAttribute("aria-label")).toBe("Restore cleared captions");
    expect(document.body.innerHTML).not.toContain("Put every caption back");
  });

  it("sits to the right of Clear captions", async () => {
    setUp(WRITTEN);
    await waitFor(() => expect(bar()).toBeTruthy());
    const inBar = Array.from(bar().children);
    const clear = inBar.findIndex((el) => el.classList.contains("clear"));
    const back = inBar.findIndex((el) => el.classList.contains("bar-back"));
    expect(clear).toBeGreaterThanOrEqual(0);
    expect(back).toBe(clear + 1);
  });

  it("leaves the money holding the right edge", async () => {
    setUp(CLEARED);
    await waitFor(() => expect(bar()).toBeTruthy());
    const inBar = Array.from(bar().children);
    expect(inBar[inBar.length - 1].classList.contains("money")).toBe(true);
  });

  it("goes grey again once there is nothing still empty to put back", async () => {
    // He typed over one after the clear and put the other back. Nothing is
    // left for this to act on, so it says so rather than sitting live and
    // doing nothing.
    setUp([
      { file: "photo-01.jpg", caption: "View east from Brady Street",
        cleared_caption: "View east from Brady Street" },
      { file: "photo-02.jpg", caption: "Something he typed himself",
        cleared_caption: "Rear loading area" },
    ]);
    await waitFor(() => expect(bar()).toBeTruthy());
    expect(barBack().disabled).toBe(true);
    // And each tile's own Back is still live, because it works on its own.
    expect(backOn(tiles()[0]).disabled).toBe(false);
    expect(backOn(tiles()[1]).disabled).toBe(false);
  });

  it("puts back the still-empty ones and leaves what he typed alone", async () => {
    setUp([
      CLEARED[0],
      { file: "photo-02.jpg", caption: "Something he typed himself",
        cleared_caption: "Rear loading area" },
    ]);
    const all = vi.spyOn(api, "captionsBack").mockResolvedValue(manifest([
      { file: "photo-01.jpg", caption: "View east from Brady Street",
        cleared_caption: "View east from Brady Street" },
      { file: "photo-02.jpg", caption: "Something he typed himself",
        cleared_caption: "Rear loading area" },
    ]));
    await waitFor(() => expect(bar()).toBeTruthy());

    await userEvent.click(barBack());

    expect(all).toHaveBeenCalledWith(JOB);
    await waitFor(() => expect(
      within(tiles()[0]).getByRole("textbox").value).toBe("View east from Brady Street"));
    expect(within(tiles()[1]).getByRole("textbox").value).toBe("Something he typed himself");
  });
});

describe("the row inside the photograph", () => {
  it("draws the tick and the band dots as the circles the app already draws", async () => {
    // Spenser, 2026-09-17: *"The actual app is circles, and you gave me
    // little ovals."* Nothing on those may gain a width of its own.
    setUp(CLEARED);
    await waitFor(() => expect(tiles().length).toBe(2));
    expect(tickOn(tiles()[0]).className.split(/\s+/)).toContain("dot");
    expect(backOn(tiles()[0]).className.split(/\s+/)).toContain("dot");
  });

  it("puts every control on the one row, in the order he drew them", async () => {
    setUp(CLEARED);
    await waitFor(() => expect(tiles().length).toBe(2));
    const row = tiles()[0].querySelector(".review-line");
    const classes = Array.from(row.children).map((el) => el.className);
    expect(classes[0]).toMatch(/tick-dot/);
    expect(classes[classes.length - 2]).toMatch(/back-dot/);
    expect(classes[classes.length - 1]).toMatch(/refresh-dot/);
  });
});
