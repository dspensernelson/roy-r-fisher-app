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
  // One place for photographs, so no question is asked. That is the state
  // every existing job and every job the app makes itself is in.
  vi.spyOn(api, "photoGroups").mockResolvedValue({
    groups: [{ folder: "", count: 3, sample: "photo-01.jpg" }],
    chosen: null, chosen_missing: false, needs_choice: false });
  vi.spyOn(api, "putPhotoGroup").mockResolvedValue({ chosen: "" });
  vi.spyOn(api, "readingProgress").mockResolvedValue(
    { reading: false, done: 0, total: 0 });
});

const TWO_PLACES = {
  groups: [
    { folder: "Raw pics_X", count: 16, sample: "IMG_0559.jpeg" },
    { folder: "Report Photos_X", count: 16, sample: "1 IMG_0559.jpeg" },
    { folder: "", count: 1, sample: "AERIAL.png" },
  ],
  chosen: null, chosen_missing: false, needs_choice: true,
};

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
    await screen.findByRole("heading", { name: "Photos" });
  });

  it("falls back to Loading before any count is known", async () => {
    let release;
    api.getManifest.mockReturnValue(new Promise((r) => { release = r; }));
    render(<PhotosScreen job={JOB} />);
    expect(await screen.findByText("Loading...")).toBeInTheDocument();
    release(manifest());
    await screen.findByRole("heading", { name: "Photos" });
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
    expect(await screen.findByText(/1 photograph is waiting for a band/)).toBeInTheDocument();
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
  it("starts off, with no chips, on a job that has never used bands", async () => {
    await show();
    expect(await screen.findByRole("button", { name: "Off" })).toHaveAttribute(
      "aria-pressed", "true");
    expect(screen.queryAllByRole("button", { name: /^Band [ABC]$/ })).toHaveLength(0);
  });

  it("asks the server to turn them on, and shows what comes back", async () => {
    const put = vi.spyOn(api, "putBands").mockResolvedValue(banded());
    await show();
    await userEvent.click(await screen.findByRole("button", { name: "On" }));
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
    await userEvent.click(await screen.findByRole("button", { name: "Off" }));
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
    await userEvent.click(await screen.findByRole("button", { name: "On" }));
    await screen.findByRole("button", { name: "Band A" });
    const captions = screen.getAllByRole("textbox");
    expect(captions).toHaveLength(order.length);
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

  it("counts three to a page while three is chosen", async () => {
    api.getManifest.mockResolvedValue(manifest({ photos: photos(12), photos_per_page: 3 }));
    await show();
    expect(await screen.findByText(/about 4 pages/)).toBeInTheDocument();
  });

  it("halves the page count when six is chosen", async () => {
    api.getManifest.mockResolvedValue(manifest({ photos: photos(12), photos_per_page: 6 }));
    await show();
    expect(await screen.findByText(/about 2 pages/)).toBeInTheDocument();
  });

  it("says one page rather than one pages", async () => {
    api.getManifest.mockResolvedValue(manifest({ photos: photos(5), photos_per_page: 6 }));
    await show();
    expect(await screen.findByText(/about 1 page\./)).toBeInTheDocument();
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
