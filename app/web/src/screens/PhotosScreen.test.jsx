import React from "react";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
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
    blocked_because: "",
    // The first three photographs, captioned in both styles, which is what
    // the chooser offers to show him. Six photographs are paid for.
    samples: { photos: 3, styles: 2,
               estimate: { label: "Estimated maximum cost", photos: 6, rate: 0.05,
                           total: 0.30, arithmetic: "6 x $0.0500 = $0.30",
                           is_estimate: true } },
    ...over,
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
  // One place for photographs, so no question is asked. That is the state
  // every existing job and every job the app makes itself is in.
  vi.spyOn(api, "photoGroups").mockResolvedValue({
    groups: [{ folder: "", count: 3, sample: "photo-01.jpg" }],
    chosen: null, chosen_missing: false, needs_choice: false });
  vi.spyOn(api, "putPhotoGroup").mockResolvedValue({ chosen: "" });
  vi.spyOn(api, "readingProgress").mockResolvedValue(
    { reading: false, done: 0, total: 0 });
  // The style window writes captions from his first photographs as it opens,
  // so every test that opens it answers that call. Nothing here by default.
  vi.spyOn(api, "captionSamples").mockResolvedValue(
    { ai_available: true, photos: [], samples: {} });
});

const TWO_PLACES = {
  groups: [
    { folder: "Raw pics_X", count: 16, sample: "IMG_0559.jpeg" },
    { folder: "Report Photos_X", count: 16, sample: "1 IMG_0559.jpeg" },
    { folder: "", count: 1, sample: "AERIAL.png" },
  ],
  chosen: null, chosen_missing: false, needs_choice: true,
};

// Superseded on 2026-09-15 by the approved design. The screen used to be
// titled `Photos`; it is now titled with the name of the document it makes, so
// waiting on that one word no longer works. The folder question, which is
// asked before any document is in view, still calls itself Photos.
async function show() {
  render(<PhotosScreen job={JOB} />);
  await screen.findByRole("heading");
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
  it("shows the written examples while his own are being written", async () => {
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

  // Superseded on 2026-09-15 by the approved design. The money used to be
  // asked for in a second window that opened on top of the style window, and
  // said the same figure twice on it. There is one window now: it carries the
  // count, the figure, the style and the go-ahead, and cancelling it is still
  // the thing that must send nothing.
  it("asks before anything is sent, and cancelling sends nothing", async () => {
    vi.spyOn(api, "draftCaptions").mockResolvedValue({});
    await show();
    await userEvent.click(await screen.findByRole("button", { name: /Generate captions/ }));

    expect(await screen.findByText(/Generate captions for 61 photos\?/)).toBeInTheDocument();
    expect(document.querySelector(".sheet-cost").textContent).toBe("$3.05 max");
    expect(screen.getByRole("button", { name: "Generate captions ($3.05)" }))
      .toBeInTheDocument();

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

  // Superseded on 2026-09-15 by the approved design. `Use this style` was the
  // button on the old style window; the one window is finished by the button
  // that spends the money, which names the amount.
  async function runIt() {
    await show();
    await userEvent.click(await screen.findByRole("button", { name: /Generate captions/ }));
    await userEvent.click(await screen.findByRole("button", { name: /^Generate captions \(\$/ }));
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

  // Superseded on 2026-09-15 by the approved design. There were two boxes
  // saying where the file would go and then where it went, and the first had
  // to disappear when the second arrived. The name is the screen's title now,
  // so it is said once, always, and the build says only that it is ready.
  it("says the name once, as the title, before and after the build", async () => {
    const named = "Anytown_100 Example Avenue Photos (Complete).docx";
    await show();
    expect(await screen.findByRole("heading", { name: named })).toBeInTheDocument();
    expect(screen.queryByText(/Will be saved as/)).toBeNull();
    await userEvent.click(await screen.findByRole("button", { name: "Build photo pages" }));
    await screen.findByRole("button", { name: "Open document" });
    expect(screen.getByRole("heading", { name: named })).toBeInTheDocument();
    expect(screen.queryByText(/Will be saved as/)).toBeNull();
  });
});

describe("build is gated on review", () => {
  it("is off until every caption has been read", async () => {
    await show();
    expect(await screen.findByText(/0 of 3 reviewed/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Build photo pages" })).toBeDisabled();
  });

  // Superseded on 2026-09-15 by the approved design. The line used to read
  // "3 of 3 reviewed. Ready to build." Nothing is happening once they are all
  // read, so nothing is said: the quiet line goes empty and the live Build
  // button is the whole of the news.
  it("comes alive when they all have, and stops talking about it", async () => {
    api.getManifest.mockResolvedValue(manifest({ photos: photos(3, "View of something") }));
    await show();
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Build photo pages" })).toBeEnabled());
    expect(screen.queryByText(/reviewed/)).toBeNull();
    expect(document.querySelector(".quiet").textContent).toBe("");
  });
});

describe("the cost confirmation cannot be skipped", () => {
  it("will not start a run before the estimate has arrived", async () => {
    // The estimate never resolves, which is what a slow one looks like for the
    // moment it is slow. The button counted the photographs itself and went
    // live, so a 61-photo run could start with no confirmation shown.
    api.getManifest.mockResolvedValue(manifest({ photos: photos(61) }));
    api.captionEstimate.mockReturnValue(new Promise(() => {}));
    vi.spyOn(api, "draftCaptions").mockResolvedValue({});

    await show();
    const button = await screen.findByRole("button", { name: /Generate captions/ });
    expect(button).toBeDisabled();
    await userEvent.click(button);
    expect(api.draftCaptions).not.toHaveBeenCalled();
  });

  it("comes alive with the count once the estimate is in", async () => {
    api.getManifest.mockResolvedValue(manifest({ photos: photos(61) }));
    api.captionEstimate.mockResolvedValue(estimate({
      photos_to_send: 61, tranches: 2, needs_confirmation: true }));
    await show();
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Generate captions (61)" })).toBeEnabled());
  });
});

describe("where a photograph came from", () => {
  // The app reads subfolders of Photos now, because four of the nine real
  // jobs keep every photograph in one. That means a tile can be a photograph
  // out of a folder called "Do Not Use", and Mark has to be able to see that
  // without opening anything. The app deliberately does not act on the name
  // itself: what "Used" and "Do Not Use" mean is his to say, not ours to
  // guess, so it shows him the folder and leaves the cutting to him.
  it("says which folder a photograph came from", async () => {
    api.getManifest.mockResolvedValue(manifest({
      photos: [{ file: "a.jpeg", caption: "", folder: "Raw pics_Somewhere/Do Not Use" }],
    }));
    render(<PhotosScreen job={JOB} />);
    expect(await screen.findByText(/from Do Not Use/)).toBeInTheDocument();
  });

  it("shows the leaf folder, not the whole path", async () => {
    const folder = "Raw pics_Walmart Mason City 4151 4th St SW/All report photos used";
    api.getManifest.mockResolvedValue(manifest({
      photos: [{ file: "a.jpeg", caption: "", folder }],
    }));
    render(<PhotosScreen job={JOB} />);
    const label = await screen.findByText(/from All report photos used/);
    // The whole path is the tooltip, so nothing is lost by shortening it.
    expect(label).toHaveAttribute("title", folder);
  });

  it("says nothing at all for a photograph at the top of Photos", async () => {
    render(<PhotosScreen job={JOB} />);      // the default manifest has no folder
    await screen.findAllByPlaceholderText("Caption...");
    expect(screen.queryByText(/^from /)).not.toBeInTheDocument();
  });
});


describe("which folder holds the report photographs", () => {
  // Mark's office keeps every shoot twice, full size and shrunk by hand, and
  // names the folders differently every job. Eleven real jobs, nine namings,
  // and a new helper has just added a tenth. So the app shows him the folders
  // his own office made and he says which one is the report.

  it("asks nothing when the photographs are all in one place", async () => {
    await show();
    expect(screen.queryByText(/Which folder holds the photographs/)).not.toBeInTheDocument();
    expect(await screen.findAllByPlaceholderText("Caption...")).toHaveLength(3);
  });

  it("asks instead of showing the photographs when there is more than one place", async () => {
    api.photoGroups.mockResolvedValue(TWO_PLACES);
    await show();
    expect(await screen.findByText(/Which folder holds the photographs/)).toBeInTheDocument();
    expect(screen.queryByPlaceholderText("Caption...")).not.toBeInTheDocument();
  });

  it("shows each folder by its real name and its count", async () => {
    api.photoGroups.mockResolvedValue(TWO_PLACES);
    await show();
    expect(await screen.findByText("Report Photos_X")).toBeInTheDocument();
    expect(screen.getByText("Raw pics_X")).toBeInTheDocument();
    expect(screen.getAllByText("16 photographs")).toHaveLength(2);
    expect(screen.getByText("1 photograph")).toBeInTheDocument();
  });

  it("names the top of Photos in words rather than leaving it blank", async () => {
    api.photoGroups.mockResolvedValue(TWO_PLACES);
    await show();
    expect(await screen.findByText("The Photos folder itself")).toBeInTheDocument();
  });

  it("records his answer and then shows the photographs", async () => {
    api.photoGroups.mockResolvedValue(TWO_PLACES);
    await show();
    await userEvent.click(await screen.findByText("Report Photos_X"));
    expect(api.putPhotoGroup).toHaveBeenCalledWith(JOB, "Report Photos_X");
  });

  it("says where the report photographs came from once he has chosen", async () => {
    api.photoGroups.mockResolvedValue({
      ...TWO_PLACES, chosen: "Report Photos_X", needs_choice: false });
    await show();
    expect(await screen.findByText(/Use a different folder/)).toBeInTheDocument();
    expect(screen.getAllByPlaceholderText("Caption...")).toHaveLength(3);
  });

  // "" and null are different answers. "" is the top of Photos and is a
  // decision; null means he has never been asked. A screen that tests the
  // name for letters reads his decision as no decision and then shows him
  // no way back to the question.
  it("still offers the way back when he chose the top of Photos", async () => {
    api.photoGroups.mockResolvedValue({
      ...TWO_PLACES, chosen: "", needs_choice: false });
    await show();
    expect(await screen.findByText(/Use a different folder/)).toBeInTheDocument();
    expect(screen.getByText("the Photos folder itself")).toBeInTheDocument();
  });

  it("lets him ask again without losing what he already chose", async () => {
    api.photoGroups.mockResolvedValue({
      ...TWO_PLACES, chosen: "Report Photos_X", needs_choice: false });
    await show();
    await userEvent.click(await screen.findByText(/Use a different folder/));
    expect(await screen.findByText(/Which folder holds the photographs/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Cancel" })).toBeInTheDocument();
  });

  it("says plainly when the folder he chose is gone, and never picks another", async () => {
    api.photoGroups.mockResolvedValue({
      ...TWO_PLACES, chosen: "Final Photos", chosen_missing: true,
      needs_choice: false });
    await show();
    expect(await screen.findByText(/is not in this job any more/)).toBeInTheDocument();
    expect(screen.getByText(/Nothing has been built from a different folder/)).toBeInTheDocument();
    expect(screen.queryByPlaceholderText("Caption...")).not.toBeInTheDocument();
  });
});


describe("the words on the screen", () => {
  // The right hand side is not the report. It is what the report gets made
  // out of. So a photograph is taken out of it, not cut from a report that
  // does not exist until he presses Build. Spenser's call, 2026-08-25.
  it("offers to take a photograph out, not to cut it from a report", async () => {
    await show();
    expect(await screen.findAllByRole("button", { name: "Take out" })).toHaveLength(3);
    expect(screen.queryByRole("button", { name: "Cut from report" })).not.toBeInTheDocument();
  });

  it("calls the section below Taken out", async () => {
    api.getManifest.mockResolvedValue(manifest({
      photos: [{ file: "a.jpg", caption: "" }, { file: "b.jpg", caption: "", cut: true }],
    }));
    await show();
    expect(await screen.findByRole("button", { name: /Taken out \(1\)/ })).toBeInTheDocument();
  });
});


// --- what the screen says while it waits, and when it cannot ---------------
// Two faults, one screen. It said nothing while it worked, and it hid the
// reason when it failed. The second one cost Colleen a morning on 2026-09-03:
// the photo list could not be read, the error was caught and stored, and the
// screen returned `Loading...` above every line that could have shown it.

describe("while it is waiting for the photo list", () => {
  it("says which photograph it has got to, not just Loading", async () => {
    let release;
    api.getManifest.mockReturnValue(new Promise((r) => { release = r; }));
    api.readingProgress.mockResolvedValue({ reading: true, done: 40, total: 131 });

    render(<PhotosScreen job={JOB} />);
    expect(await screen.findByText(/Reading photograph 40 of 131/)).toBeInTheDocument();

    release(manifest());
    // Superseded on 2026-09-15: the screen is titled by the document it makes.
    await screen.findByRole("heading");
  });

  it("falls back to Loading before any count is known", async () => {
    let release;
    api.getManifest.mockReturnValue(new Promise((r) => { release = r; }));
    render(<PhotosScreen job={JOB} />);
    expect(await screen.findByText("Loading...")).toBeInTheDocument();
    release(manifest());
    // Superseded on 2026-09-15: the screen is titled by the document it makes.
    await screen.findByRole("heading");
  });

  it("stops asking once the list arrives", async () => {
    await show();
    const asked = api.readingProgress.mock.calls.length;
    await new Promise((r) => setTimeout(r, 900));
    expect(api.readingProgress.mock.calls.length).toBe(asked);
  });
});

describe("when the photo list cannot be read", () => {
  it("shows the reason instead of sitting on Loading for ever", async () => {
    api.getManifest.mockRejectedValue(
      new Error("photo-manifest.json is not valid JSON. Fix the file or delete it and try again."));

    render(<PhotosScreen job={JOB} />);
    expect(await screen.findByText(/photo-manifest.json is not valid JSON/))
      .toBeInTheDocument();
    expect(screen.queryByText("Loading...")).not.toBeInTheDocument();
  });

  it("says nothing has been changed, and where to send it", async () => {
    api.getManifest.mockRejectedValue(new Error("Something went wrong."));
    render(<PhotosScreen job={JOB} />);
    expect(await screen.findByText(/Nothing has been changed/)).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// Bands. One click per photograph instead of one drag per photograph.
//
// The tick sits at the lower left of every tile, whether bands are on or off,
// so it keeps one place however many bands a job grows. Spenser, 2026-09-07.
// ---------------------------------------------------------------------------

const BANDS = [
  { letter: "A", name: "A", locked: true },
  { letter: "B", name: "B", locked: true },
  { letter: "C", name: "C", locked: true },
];

function banded(over = {}) {
  return manifest({ bands_on: true, bands: BANDS, ...over });
}

describe("bands", () => {
  it("shows the tick and no dots while the switch is off", async () => {
    await show();
    expect(await screen.findAllByRole("button", { name: /^Mark reviewed$/ }))
      .toHaveLength(3);
    expect(screen.queryAllByRole("button", { name: /^Put in band / })).toHaveLength(0);
  });

  it("gives every photograph one dot per band once the switch is on", async () => {
    api.getManifest.mockResolvedValue(banded());
    await show();
    // three photographs, three bands
    expect(await screen.findAllByRole("button", { name: "Put in band A" })).toHaveLength(3);
    expect(screen.getAllByRole("button", { name: "Put in band C" })).toHaveLength(3);
    // and the tick has not gone anywhere
    expect(screen.getAllByRole("button", { name: /^Mark reviewed$/ })).toHaveLength(3);
  });

  it("puts the photograph in the band he clicks", async () => {
    api.getManifest.mockResolvedValue(banded());
    const set = vi.spyOn(api, "setPhotoBand").mockResolvedValue(
      banded({ photos: [{ file: "photo-01.jpg", caption: "", band: "A" },
                        { file: "photo-02.jpg", caption: "" },
                        { file: "photo-03.jpg", caption: "" }] }));
    await show();
    await userEvent.click((await screen.findAllByRole("button", { name: "Put in band A" }))[0]);
    expect(set).toHaveBeenCalledWith(JOB, "photo-01.jpg", "A");
  });

  it("holds the build while photographs are still waiting for a band", async () => {
    api.getManifest.mockResolvedValue(banded({
      photos: [{ file: "photo-01.jpg", caption: "one", reviewed: true },
               { file: "photo-02.jpg", caption: "two", reviewed: true, band: "A" },
               { file: "photo-03.jpg", caption: "three", reviewed: true, band: "C" }],
    }));
    await show();
    // Superseded on 2026-09-15: the reason is on the quiet line AND on the
    // button it blocks, which is where what stops an action is said. So the
    // line is read out of the quiet line rather than off the whole screen.
    const said = await screen.findByText(/1 photograph is waiting for a band/,
                                         { selector: ".said" });
    expect(said).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Build photo pages" })).toBeDisabled();
  });

  it("lets the build go once every photograph has a band", async () => {
    api.getManifest.mockResolvedValue(banded({
      photos: [{ file: "photo-01.jpg", caption: "one", reviewed: true, band: "A" },
               { file: "photo-02.jpg", caption: "two", reviewed: true, band: "A" },
               { file: "photo-03.jpg", caption: "three", reviewed: true, band: "C" }],
    }));
    await show();
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Build photo pages" })).toBeEnabled());
    expect(screen.queryByText(/waiting for a band/)).not.toBeInTheDocument();
  });

  it("says nothing about waiting while the switch is off", async () => {
    api.getManifest.mockResolvedValue(manifest({
      photos: [{ file: "photo-01.jpg", caption: "one", reviewed: true },
               { file: "photo-02.jpg", caption: "two", reviewed: true },
               { file: "photo-03.jpg", caption: "three", reviewed: true }],
    }));
    await show();
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Build photo pages" })).toBeEnabled());
    expect(screen.queryByText(/waiting for a band/)).not.toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// The switch. Bands are off until Mark turns them on, and 0.6.7 shipped with
// no way to do it. Spenser's design, 2026-09-07: a pill reading Bands On or
// Off, and once it is on, the chips A, B and C to the right of it.
// ---------------------------------------------------------------------------

describe("the bands switch", () => {
  // Superseded on 2026-09-15 by the approved design. Bands was a pair of
  // pills reading On and Off, identical to the pair beside it that chose
  // three or six to a page. Two controls doing different jobs do not look the
  // same, so bands is a switch now. What it does has not changed.
  it("starts off, with no chips, on a job that has never used bands", async () => {
    await show();
    expect(await screen.findByRole("switch", { name: "Bands" }))
      .toHaveAttribute("aria-checked", "false");
    expect(screen.queryAllByRole("button", { name: /^Band [ABC]$/ })).toHaveLength(0);
  });

  it("asks the server to turn them on, and shows what comes back", async () => {
    const put = vi.spyOn(api, "putBands").mockResolvedValue(banded());
    await show();
    await userEvent.click(await screen.findByRole("switch", { name: "Bands" }));
    expect(put).toHaveBeenCalledWith(JOB, { bands_on: true });
    expect(await screen.findByRole("button", { name: "Band A" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Band B" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Band C" })).toBeInTheDocument();
  });

  it("asks the server to turn them off, and the dots go", async () => {
    api.getManifest.mockResolvedValue(banded());
    const put = vi.spyOn(api, "putBands").mockResolvedValue(
      manifest({ bands_on: false, bands: BANDS }));
    await show();
    await userEvent.click(await screen.findByRole("switch", { name: "Bands" }));
    expect(put).toHaveBeenCalledWith(JOB, { bands_on: false });
    await waitFor(() =>
      expect(screen.queryAllByRole("button", { name: /^Put in band / })).toHaveLength(0));
  });

  it("moves no photograph of its own accord", async () => {
    // Constraint 1. The screen redraws from what the server sent back and
    // sorts nothing itself.
    const order = ["photo-01.jpg", "photo-02.jpg", "photo-03.jpg"];
    vi.spyOn(api, "putBands").mockResolvedValue(banded());
    await show();
    await userEvent.click(await screen.findByRole("switch", { name: "Bands" }));
    await screen.findByRole("button", { name: "Band A" });
    const captions = screen.getAllByRole("textbox");
    expect(captions).toHaveLength(order.length);
  });
});

// ---------------------------------------------------------------------------
// Mark all as reviewed, behind a warning.
//
// Spenser's rule, 2026-09-03, in his own words: it is very important that
// humans review everything AI does. So this is never a plain button. The
// warning says what it removes, and he chooses.
// ---------------------------------------------------------------------------

const UNREAD = [
  { file: "photo-01.jpg", caption: "one" },
  { file: "photo-02.jpg", caption: "two" },
  { file: "photo-03.jpg", caption: "three" },
];

describe("marking every caption reviewed", () => {
  beforeEach(() => {
    api.getManifest.mockResolvedValue(manifest({ photos: UNREAD }));
  });

  it("offers it while something is still unread", async () => {
    await show();
    expect(await screen.findByRole("button", { name: "Mark all as reviewed" }))
      .toBeInTheDocument();
  });

  it("asks first, and calls nobody until he says yes", async () => {
    const all = vi.spyOn(api, "markAllReviewed").mockResolvedValue({});
    await show();
    await userEvent.click(await screen.findByRole("button", { name: "Mark all as reviewed" }));
    expect(await screen.findByText(/removes the human check/)).toBeInTheDocument();
    expect(all).not.toHaveBeenCalled();
  });

  it("backs out without calling anybody", async () => {
    const all = vi.spyOn(api, "markAllReviewed").mockResolvedValue({});
    await show();
    await userEvent.click(await screen.findByRole("button", { name: "Mark all as reviewed" }));
    await userEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(all).not.toHaveBeenCalled();
    expect(screen.queryByText(/removes the human check/)).not.toBeInTheDocument();
  });

  it("marks them when he says yes", async () => {
    const all = vi.spyOn(api, "markAllReviewed").mockResolvedValue(
      manifest({ photos: UNREAD.map((p) => ({ ...p, reviewed: true })) }));
    await show();
    await userEvent.click(await screen.findByRole("button", { name: "Mark all as reviewed" }));
    await userEvent.click(screen.getByRole("button", { name: "Mark them all" }));
    expect(all).toHaveBeenCalledWith(JOB);
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Build photo pages" })).toBeEnabled());
  });

  it("does not offer it once every caption is read", async () => {
    api.getManifest.mockResolvedValue(manifest({
      photos: UNREAD.map((p) => ({ ...p, reviewed: true })) }));
    await show();
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Build photo pages" })).toBeEnabled());
    expect(screen.queryByRole("button", { name: "Mark all as reviewed" }))
      .not.toBeInTheDocument();
  });
});

describe("three or six to a page", () => {
  it("starts on three, which is what every job that never chose is", async () => {
    api.getManifest.mockResolvedValue(manifest({ photos_per_page: 3 }));
    await show();
    expect(await screen.findByRole("button", { name: "Three photographs to a page" }))
      .toHaveAttribute("aria-pressed", "true");
    expect(screen.getByRole("button", { name: "Six photographs to a page" }))
      .toHaveAttribute("aria-pressed", "false");
  });

  // Superseded on 2026-09-15 by the approved design. The count used to read
  // "about 4 pages". The app knows the layout, so a number it knows exactly
  // is stated exactly: twelve photographs at three to a page is four pages.
  it("counts three to a page while three is chosen", async () => {
    api.getManifest.mockResolvedValue(manifest({ photos: photos(12), photos_per_page: 3 }));
    await show();
    expect(await screen.findByText(/12 photographs · 4 pages/)).toBeInTheDocument();
  });

  it("halves the page count when six is chosen", async () => {
    api.getManifest.mockResolvedValue(manifest({ photos: photos(12), photos_per_page: 6 }));
    await show();
    expect(await screen.findByText(/12 photographs · 2 pages/)).toBeInTheDocument();
  });

  it("says one page rather than one pages", async () => {
    api.getManifest.mockResolvedValue(manifest({ photos: photos(5), photos_per_page: 6 }));
    await show();
    expect(await screen.findByText(/5 photographs · 1 page$/)).toBeInTheDocument();
  });

  it("writes the choice into the manifest and nothing else", async () => {
    const before = manifest({ photos: photos(6), photos_per_page: 3 });
    api.getManifest.mockResolvedValue(before);
    const put = vi.spyOn(api, "putManifest")
      .mockResolvedValue({ ok: true });
    await show();
    await userEvent.click(await screen.findByRole("button", { name: "Six photographs to a page" }));
    expect(put).toHaveBeenCalledWith(JOB, { ...before, photos_per_page: 6 });
  });

  it("leaves the photographs alone", async () => {
    // The toggle changes what Build makes. It must not touch the list, the
    // order, or a single caption.
    const names = () => screen.getAllByRole("img").map((i) => i.getAttribute("alt"));
    const captions = () => screen.getAllByRole("textbox").map((t) => t.value);
    api.getManifest.mockResolvedValue(manifest({ photos: photos(6, "a caption") }));
    await show();
    const wasOrder = names();
    const wasCaptions = captions();
    await userEvent.click(screen.getByRole("button", { name: "Six photographs to a page" }));
    await waitFor(() => expect(names()).toEqual(wasOrder));
    expect(captions()).toEqual(wasCaptions);
  });
});

describe("the caption chooser's page preview", () => {
  // Its own comment promises it is drawn "exactly the way photo_pages.py
  // builds the real thing". A second layout is what makes that promise
  // testable rather than decorative.
  async function openChooser(perPage) {
    api.getManifest.mockResolvedValue(manifest({ photos: photos(3), photos_per_page: perPage }));
    await show();
    await userEvent.click(await screen.findByRole("button", { name: /Generate captions/ }));
    return screen.findByTestId("page-preview");
  }

  it("draws one photograph beside its caption at three to a page", async () => {
    const grid = await openChooser(3);
    expect(grid).not.toHaveClass("is-six");
    expect(grid.querySelectorAll(".cell-photo.is-example").length)
      .toBe(grid.querySelectorAll(".cell-caption:not(.head)").length);
  });

  it("draws two photographs above their two captions at six to a page", async () => {
    const grid = await openChooser(6);
    expect(grid).toHaveClass("is-six");
    const kids = [...grid.children].filter((el) => !el.classList.contains("head"));
    // photo photo caption caption, repeating
    expect(kids.slice(0, 4).map((el) => el.className.split(" ")[0]))
      .toEqual(["cell-photo", "cell-photo", "cell-caption", "cell-caption"]);
  });
});

// Colleen's office keeps its jobs on a disk across the network. Every price
// question opens photograph files on that disk, so a question per letter typed
// is a network read per letter typed. On 2026-09-14 that stopped her screen
// answering. The price counts photographs that still need a caption, and that
// count cannot change until the caption is saved, so the question belongs on
// the save and not on the keystroke.
describe("typing a caption", () => {
  it("asks the server for the price no more while she types", async () => {
    await show();
    const boxes = await screen.findAllByPlaceholderText("Caption...");
    await waitFor(() => expect(api.captionEstimate).toHaveBeenCalled());
    api.captionEstimate.mockClear();

    await userEvent.type(boxes[0], "View of the front entrance");

    expect(api.captionEstimate).not.toHaveBeenCalled();
  });

  // Superseded on 2026-09-14. This used to assert that leaving the box asked
  // the server for the price. Spenser's rule now is that the price is asked
  // for twice and only twice, on opening the screen and on opening the step
  // that spends the money. What leaving the box must still do is save.
  it("saves what she typed when she leaves the box, and asks no price", async () => {
    await show();
    const boxes = await screen.findAllByPlaceholderText("Caption...");
    await waitFor(() => expect(api.captionEstimate).toHaveBeenCalled());
    api.captionEstimate.mockClear();

    await userEvent.type(boxes[0], "View of the front entrance");
    await userEvent.tab();

    await waitFor(() => expect(api.putManifest).toHaveBeenCalledTimes(1));
    expect(api.putManifest.mock.calls[0][1].photos[0].caption)
      .toBe("View of the front entrance");
    expect(api.captionEstimate).not.toHaveBeenCalled();
  });
});

// B13. He types a caption and reaches straight for the tick, with no click in
// between. `Mark reviewed` reads the job's list on the server, ticks the
// photograph and answers with what it read, and that answer is what the
// screen draws. Saving the caption is a separate round trip, and nothing
// orders the two, so the tick can be answered from the caption the server
// still has. Found by Spenser, 2026-09-07.
describe("ticking a caption he has just typed", () => {
  // The server, in the small, with the one property that matters here: a save
  // is in the air for a while, and until it lands the server still holds the
  // old caption. `landSave` is the save arriving. Anything the screen sends
  // before that is answered out of the old caption.
  let held = null;
  let landSave = null;

  function fakeServer(start) {
    held = structuredClone(start);
    landSave = null;
    api.getManifest.mockResolvedValue(structuredClone(held));
    api.putManifest.mockImplementation((_job, sent) => {
      const written = structuredClone(sent);
      return new Promise((resolve) => {
        landSave = () => { held = written; resolve({ ok: true }); };
      });
    });
    vi.spyOn(api, "markReviewed").mockImplementation((_job, file) => {
      const answer = structuredClone(held);
      answer.photos.find((p) => p.file === file).reviewed = true;
      held = structuredClone(answer);
      return Promise.resolve(answer);
    });
  }

  it("keeps what he typed", async () => {
    fakeServer(manifest({ photos: [
      { file: "photo-01.jpg", caption: "View of the front" },
      { file: "photo-02.jpg", caption: "View of the rear" },
    ] }));
    await show();
    const boxes = await screen.findAllByPlaceholderText("Caption...");

    await userEvent.type(boxes[0], " entrance");
    // straight from the box to the tick, with nothing clicked in between
    await userEvent.click(
      screen.getAllByRole("button", { name: /^Mark reviewed$/ })[0]);
    // the caption reaches the server, some time after he clicked
    landSave();

    await waitFor(() =>
      expect(screen.getAllByRole("button", { name: "Reviewed" })).toHaveLength(1));
    expect(api.markReviewed).toHaveBeenCalledWith(JOB, "photo-01.jpg");
    expect(screen.getAllByPlaceholderText("Caption...")[0])
      .toHaveValue("View of the front entrance");
  });
});

// The price is what a captioning run would cost. Spenser, 2026-09-14: it is an
// approximate number, it belongs on the button and inside the step that spends
// the money, and nothing else he does should make the app work it out again.
// Each time it does, the server counts photographs without captions, and
// counting them opens files on the office network disk.
describe("asking the server what a run would cost", () => {
  it("asks once when the screen opens", async () => {
    await show();
    await waitFor(() => expect(api.captionEstimate).toHaveBeenCalledTimes(1));
  });

  it("does not ask again when a photograph is ticked", async () => {
    // Captions already written, because the tick refuses until one exists.
    const written = manifest({ photos: [
      { file: "photo-01.jpg", caption: "View of the front" },
      { file: "photo-02.jpg", caption: "View of the rear" },
    ] });
    api.getManifest.mockResolvedValue(structuredClone(written));
    vi.spyOn(api, "markReviewed").mockImplementation((_job, file) => {
      const answer = structuredClone(written);
      answer.photos.find((p) => p.file === file).reviewed = true;
      return Promise.resolve(answer);
    });
    await show();
    await screen.findAllByPlaceholderText("Caption...");
    await waitFor(() => expect(api.captionEstimate).toHaveBeenCalled());
    api.captionEstimate.mockClear();

    await userEvent.click(
      screen.getAllByRole("button", { name: /^Mark reviewed$/ })[0]);

    await waitFor(() => expect(api.markReviewed).toHaveBeenCalled());
    expect(api.captionEstimate).not.toHaveBeenCalled();
  });

  it("asks again when the step that spends the money opens", async () => {
    await show();
    await waitFor(() => expect(api.captionEstimate).toHaveBeenCalled());
    api.captionEstimate.mockClear();

    await userEvent.click(
      await screen.findByRole("button", { name: /Generate captions/ }));

    await waitFor(() => expect(api.captionEstimate).toHaveBeenCalledTimes(1));
  });
});

// Spenser looked at the caption style chooser on 2026-09-14 and said it is
// ugly as fuck. These hold the five things he asked for on 2026-09-04, which
// are written down in docs/THE-WALK-2026-09-04.md under click 8.
describe("the caption style chooser he complained about", () => {
  const SAMPLES = {
    ai_available: true,
    photos: [{ file: "photo-01.jpg" }, { file: "photo-02.jpg" }, { file: "photo-03.jpg" }],
    samples: {
      view: [
        { file: "photo-01.jpg", caption: "View of the north elevation" },
        { file: "photo-02.jpg", caption: "View of the entry lobby" },
        { file: "photo-03.jpg", caption: "View of the rear yard" },
      ],
      category: [
        { file: "photo-01.jpg", caption: "Building exterior – north elevation" },
        { file: "photo-02.jpg", caption: "Common area – entry lobby" },
        { file: "photo-03.jpg", caption: "Site – rear yard" },
      ],
    },
    measured: { label: "Calculated API cost from measured usage",
                calculated_cost: 0.0211, tokens: { input: 1, output: 1 } },
  };

  // Superseded on 2026-09-15 by the approved design. The window was called
  // "How should the captions read?" and a second window opened on top of it
  // to ask for the money. There is one window now, and it is named by what
  // pressing it will do.
  async function openIt() {
    await show();
    await userEvent.click(await screen.findByRole("button", { name: /Generate captions/ }));
    return screen.findByRole("dialog", { name: "Generate captions for 3 photos?" });
  }

  it("puts the estimated maximum cost in the upper right, on one line", async () => {
    const sheet = await openIt();
    const head = sheet.querySelector(".sheet-head");
    const cost = head.querySelector(".sheet-cost");
    expect(cost).not.toBeNull();
    // One line, and now three words. It was three stacked lines: "Est. max",
    // the figure, the count. Superseded on 2026-09-15: the count moved into
    // the window's own title, so the corner carries the figure alone.
    expect(cost.textContent).toBe("$0.15 max");
    expect(cost.children).toHaveLength(0);
    // It is a number he glances at. Not the boxed callout with the red bar.
    expect(cost.closest(".confirm")).toBeNull();
    // Last in the head row, which is what puts it on the right.
    expect(head.lastElementChild).toBe(cost);
  });

  it("never calls anything suggested", async () => {
    const sheet = await openIt();
    expect(sheet.textContent).not.toMatch(/suggested/i);
    expect(sheet.querySelector(".toggle-flag")).toBeNull();
  });

  // Superseded on 2026-09-15 by the approved design. The promise under the
  // samples is gone entirely. The window's own title says how many
  // photographs it is about to caption, out of a job that holds more, so the
  // sentence saying captioned ones are skipped was the same fact in words.
  it("makes no promises under the samples at all", async () => {
    const sheet = await openIt();
    expect(sheet.textContent).not.toMatch(/Anthropic/);
    expect(sheet.querySelector(".keep-note")).toBeNull();
    expect(sheet.textContent).not.toMatch(/are never changed/);
    expect(sheet.textContent).not.toMatch(/charged for again/);
    expect(sheet.textContent).not.toMatch(/saved as each request finishes/);
    expect(sheet.querySelector("h2").textContent).toBe("Generate captions for 3 photos?");
  });

  // Superseded on 2026-09-15 by the approved design: the row is `.sheet-acts`
  // and the button that finishes the window names the money it spends.
  it("finishes the window from the bottom right, with Cancel to its left", async () => {
    const sheet = await openIt();
    const foot = sheet.querySelector(".sheet-acts");
    const buttons = [...foot.querySelectorAll("button")];
    const use = buttons.find((b) => b.textContent === "Generate captions ($0.15)");
    const cancel = buttons.find((b) => b.textContent === "Cancel");
    expect(buttons.indexOf(cancel)).toBeLessThan(buttons.indexOf(use));
    expect(foot.lastElementChild).toBe(use);
    // It spends nothing by itself and can be backed out of, so it is not red.
    // docs/ROADMAP.md, the colour law of 2026-09-08.
    expect(use).toHaveClass("secondary");
  });

  it("shows his own photographs when the window opens, with nothing to press", async () => {
    const ask = vi.spyOn(api, "captionSamples").mockResolvedValue(SAMPLES);
    const sheet = await openIt();

    await waitFor(() => expect(ask).toHaveBeenCalledTimes(1));
    expect(await screen.findByText("View of the north elevation")).toBeInTheDocument();
    expect(sheet.querySelectorAll(".cell-photo img").length).toBe(3);

    // The button that asked him to pay for them is gone. He authorised this
    // spend on 2026-09-04 and did not ask to be asked again.
    expect(screen.queryByRole("button", { name: /Show these on my photographs/ })).toBeNull();
    expect(sheet.querySelector(".sample-press")).toBeNull();
    expect(sheet.textContent).not.toMatch(/\$0\.30/);
  });

  it("does not buy them a second time when the window is opened again", async () => {
    const ask = vi.spyOn(api, "captionSamples").mockResolvedValue(SAMPLES);
    await openIt();
    await waitFor(() => expect(ask).toHaveBeenCalledTimes(1));

    await userEvent.keyboard("{Escape}");
    await waitFor(() => expect(screen.queryByRole("dialog")).toBeNull());
    await userEvent.click(screen.getByRole("button", { name: /Generate captions/ }));
    // Superseded on 2026-09-15: the window is named by what it will do.
    await screen.findByRole("dialog", { name: "Generate captions for 3 photos?" });

    expect(ask).toHaveBeenCalledTimes(1);
  });

  it("switches to the other style's captions of the same photographs", async () => {
    vi.spyOn(api, "captionSamples").mockResolvedValue(SAMPLES);
    await openIt();
    await screen.findByText("View of the north elevation");

    await userEvent.click(screen.getByRole("button", { name: /Location first/ }));
    expect(await screen.findByText("Building exterior – north elevation")).toBeInTheDocument();
    expect(screen.queryByText("View of the north elevation")).toBeNull();
  });

  it("keeps the written examples when the captions cannot be written", async () => {
    // No key on the machine, or a demo job. The window still has to work.
    vi.spyOn(api, "captionSamples").mockRejectedValue(
      new Error("Demo photographs stay on this computer."));
    const sheet = await openIt();

    expect(await screen.findByText("View of the front entrance")).toBeInTheDocument();
    expect(sheet.querySelectorAll(".cell-photo img")).toHaveLength(0);
    expect(await screen.findByText(/Demo photographs stay on this computer/))
      .toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// The design Spenser approved on 2026-09-15, after eight rounds of his own
// changes. Five kinds of thing and each gets one home: what is being made,
// what shapes it, what you can do, what is happening, and the photographs.
// ---------------------------------------------------------------------------

describe("the screen is named by the document it makes", () => {
  it("is titled with the file the build will write", async () => {
    await show();
    expect(await screen.findByRole("heading", {
      name: "Anytown_100 Example Avenue Photos (Complete).docx" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Photos" })).toBeNull();
  });

  it("says file name here.docx, greyed, when the name cannot be worked out", async () => {
    api.jobFacts.mockResolvedValue({
      ready: false, city: "", address: "", filename: "", missing: ["city", "street address"] });
    await show();
    const title = await screen.findByRole("heading", { name: "file name here.docx" });
    expect(title).toHaveClass("unknown");
  });

  it("puts the way to change it beside the name", async () => {
    await show();
    const title = await screen.findByRole("heading", {
      name: "Anytown_100 Example Avenue Photos (Complete).docx" });
    const beside = title.parentElement.querySelector("button");
    expect(beside).toHaveTextContent("Not right?");
  });

  it("asks for the name when it could not be read", async () => {
    api.jobFacts.mockResolvedValue({
      ready: false, city: "", address: "", filename: "", missing: ["city"] });
    await show();
    expect(await screen.findByRole("button", { name: "Enter it" })).toBeInTheDocument();
  });

  it("states the pages exactly, never about", async () => {
    api.getManifest.mockResolvedValue(manifest({ photos: photos(60), photos_per_page: 3 }));
    await show();
    expect(await screen.findByText(/60 photographs · 20 pages/)).toBeInTheDocument();
    expect(screen.queryByText(/about/)).toBeNull();
  });
});

describe("one widget, upper right", () => {
  it("holds the three actions and the two settings, in that order", async () => {
    await show();
    const widget = document.querySelector(".screen-actions.control-panel");
    const rows = widget.querySelectorAll(".w-row");
    expect(rows).toHaveLength(2);
    const acts = [...rows[0].querySelectorAll("button")].map((b) => b.textContent);
    expect(acts.slice(0, 3)).toEqual(
      ["Build photo pages", "Generate captions (3)", "Add photos"]);
    const settings = [...rows[1].children].map((el) => el.className.split(" ")[0]);
    expect(settings).toEqual(["w-name", "values", "w-sep", "w-name", "switch", "w-chips"]);
  });

  it("asks its two questions with two different controls", async () => {
    api.getManifest.mockResolvedValue(banded());
    await show();
    // Bands is on or off, so it is a switch.
    expect(await screen.findByRole("switch", { name: "Bands" }))
      .toHaveAttribute("aria-checked", "true");
    // Photographs to a page is a value, so it is a track of values.
    expect(screen.getByRole("group", { name: "Photographs to a page" }))
      .toHaveClass("values");
    expect(document.querySelector(".values [role=switch]")).toBeNull();
  });

  it("keeps the band chips' place when bands are off", async () => {
    api.getManifest.mockResolvedValue(manifest({ bands_on: false, bands: BANDS }));
    await show();
    await screen.findAllByPlaceholderText("Caption...");
    expect(document.querySelector(".w-chips")).toHaveClass("off");
    expect(screen.queryAllByRole("button", { name: /^Put in band / })).toHaveLength(0);
  });
});

describe("a message has one of two homes", () => {
  it("keeps the quiet line's slot open when there is nothing to say", async () => {
    api.getManifest.mockResolvedValue(manifest({ photos: photos(3, "View of something") }));
    await show();
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Build photo pages" })).toBeEnabled());
    const quiet = document.querySelector(".quiet");
    expect(quiet).not.toBeNull();
    expect(quiet.textContent).toBe("");
    expect(quiet.querySelector(".mark")).toBeNull();
  });

  it("says what is happening on that one line, not in a box", async () => {
    await show();
    expect(await screen.findByText(/0 of 3 reviewed/))
      .toHaveClass("said");
  });

  it("says what blocks the Build button on the Build button", async () => {
    await show();
    const why = document.querySelector(".screen-actions .act-wrap .why");
    expect(why.textContent).toMatch(/Tick every caption you have read first/);
    expect(why).toHaveAttribute("data-has", "yes");
  });

  it("puts nothing between the header and the photographs, whatever happens",
     async () => {
    // jsdom lays nothing out, so this is not a measurement of pixels. It is
    // the thing a measurement could not tell you anyway: that no state of
    // this screen can put a box, a banner or a line between the header and
    // the photographs, and that the header holds the same three slots in all
    // of them. On 2026-09-04 eleven of them could stack up there.
    const shape = () => {
      const head = document.querySelector(".screen-head");
      return {
        kids: [...head.children].map((el) => el.className),
        made: [...head.querySelector(".made").children]
          .map((el) => el.className.split(" ")[0]),
        after: head.nextElementSibling.className.split(" ")[0],
        slot: !!head.querySelector(".quiet"),
      };
    };

    await show();
    await screen.findByText(/0 of 3 reviewed/);
    const settled = shape();
    expect(settled).toEqual({
      kids: ["made", "screen-actions control-panel"],
      made: ["nameline", "figures", "quiet"],
      after: "grid",
      slot: true,
    });

    // A photograph waiting for a band.
    cleanup();
    api.getManifest.mockResolvedValue(banded({
      photos: [{ file: "photo-01.jpg", caption: "one", reviewed: true },
               { file: "photo-02.jpg", caption: "two", reviewed: true, band: "A" },
               { file: "photo-03.jpg", caption: "three", reviewed: true, band: "C" }] }));
    await show();
    await screen.findByText(/1 photograph is waiting for a band/, { selector: ".said" });
    expect(shape()).toEqual(settled);

    // No key on the computer, which used to put two grey paragraphs above the
    // photographs saying the same thing in different words.
    cleanup();
    api.getManifest.mockResolvedValue(manifest({ photos: photos(3, "a caption") }));
    api.captionStyles.mockResolvedValue({ ...STYLES, ai_available: false });
    api.captionEstimate.mockResolvedValue(estimate({ blocked_because: "no_key",
                                                     ai_available: false }));
    await show();
    await waitFor(() =>
      expect(screen.getByRole("button", { name: /Generate captions/ })).toBeDisabled());
    expect(shape()).toEqual(settled);

    // A finished build, which used to be a green box of its own.
    cleanup();
    api.captionStyles.mockResolvedValue(STYLES);
    api.captionEstimate.mockResolvedValue(estimate({ photos_to_send: 0,
                                                     blocked_because: "nothing_to_do" }));
    api.getManifest.mockResolvedValue(manifest({ photos: photos(3, "a caption") }));
    vi.spyOn(api, "build").mockResolvedValue({ created: "x.docx", folder: "/tmp" });
    await show();
    await userEvent.click(await screen.findByRole("button", { name: "Build photo pages" }));
    await screen.findByRole("button", { name: "Open document" });
    expect(shape()).toEqual(settled);
  });
});

describe("generating captions is one window", () => {
  it("asks the cost, the style and the go-ahead in the same window", async () => {
    api.getManifest.mockResolvedValue(manifest({ photos: photos(61) }));
    api.captionEstimate.mockResolvedValue(estimate({
      photos_to_send: 61, tranches: 2, needs_confirmation: true,
      estimate: { label: "Estimated maximum cost", photos: 61, rate: 0.05,
                  total: 3.05, arithmetic: "61 x $0.0500 = $3.05", is_estimate: true } }));
    vi.spyOn(api, "draftCaptions").mockResolvedValue({});
    await show();
    await userEvent.click(await screen.findByRole("button", { name: /Generate captions \(61\)/ }));

    const sheet = await screen.findByRole("dialog");
    expect(document.querySelectorAll(".sheet")).toHaveLength(1);
    expect(sheet.querySelector("h2").textContent).toBe("Generate captions for 61 photos?");
    expect(sheet.querySelector(".sheet-cost").textContent).toBe("$3.05 max");
    expect(sheet.querySelectorAll(".toggle button")).toHaveLength(2);
    const acts = [...sheet.querySelectorAll(".sheet-acts button")].map((b) => b.textContent);
    expect(acts).toEqual(["Cancel", "Generate captions ($3.05)"]);
  });

  it("opens no second window on top of it", async () => {
    api.getManifest.mockResolvedValue(manifest({ photos: photos(61) }));
    api.captionEstimate.mockResolvedValue(estimate({
      photos_to_send: 61, tranches: 2, needs_confirmation: true }));
    vi.spyOn(api, "draftCaptions").mockResolvedValue(
      manifest({ photos: photos(61, "View of something") }));
    vi.spyOn(api, "captionProgress").mockResolvedValue({ running: false });
    await show();
    await userEvent.click(await screen.findByRole("button", { name: /Generate captions \(61\)/ }));
    await userEvent.click(await screen.findByRole("button", { name: /^Generate captions \(\$/ }));
    await waitFor(() => expect(api.draftCaptions).toHaveBeenCalled());
    expect(api.draftCaptions.mock.calls[0][1]).toBe(true);
  });

  it("picks the caption style here and nowhere else", async () => {
    await show();
    await screen.findAllByPlaceholderText("Caption...");
    expect(document.querySelector(".toggle")).toBeNull();
    await userEvent.click(screen.getByRole("button", { name: /Generate captions/ }));
    expect(document.querySelectorAll(".toggle")).toHaveLength(1);
  });
});

describe("the lines he had taken out on 2026-09-15", () => {
  it("never says any of them", async () => {
    await show();
    await screen.findAllByPlaceholderText("Caption...");
    const said = document.body.textContent;
    expect(said).not.toMatch(/Drag a photo to reorder it/);
    expect(said).not.toMatch(/Build waits until you have read them all/);
    expect(said).not.toMatch(/saved as each request finishes/);
    expect(said).not.toMatch(/saved as each one finishes/);
  });
});
