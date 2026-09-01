import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";

import JobHome from "./JobHome.jsx";
import * as api from "../api.js";

const JOB = "DAVENPORT_2840 Brady Street - 2026 Tax";

const LETTER = {
  name: "Signed Engagement Letter.pdf",
  rel: "Subject Information/Signed Engagement Letter.pdf",
  within: "", kind: "file", classification: null,
};

function file(name, folder = "Photos") {
  return { name, rel: `${folder}/${name}`, within: "", kind: "file",
           classification: null };
}

function folders(over = {}) {
  return {
    typical: [{ folder: "Subject Information", count: 1, unreadable: false,
                truncated: false, kind: "folder", files: [LETTER] }],
    other: [], root_files: [], missing_classifications: [], ...over,
  };
}

// A folder holding three photographs and one PDF, which is the mixed case.
const MIXED = [file("IMG_0001.jpeg"), file("IMG_0002.jpeg"),
               file("IMG_0003.jpeg"), file("Scan.pdf")];

function photosFolder() {
  return folders({
    typical: [{ folder: "Photos", count: 4, unreadable: false,
                truncated: false, kind: "folder", files: MIXED }],
  });
}

async function openPhotos() {
  render(<JobHome job={JOB} onOpenSection={() => {}} onEditSections={() => {}} />);
  await screen.findByRole("heading", { name: JOB });
  await userEvent.click(await screen.findByText("Photos"));
}

beforeEach(() => {
  vi.spyOn(api, "jobDetail").mockResolvedValue({
    name: JOB, photo_count: 12, context: "", engagement: "", sections: [] });
  vi.spyOn(api, "jobFolders").mockResolvedValue(folders());
  vi.spyOn(api, "classificationLabels").mockResolvedValue({
    labels: ["Engagement letter", "Subject photograph"] });
  vi.spyOn(api, "setClassification").mockResolvedValue({ ok: true });
  vi.spyOn(api, "clearClassification").mockResolvedValue({ ok: true });
  vi.spyOn(api, "setClassifications").mockResolvedValue({
    applied: ["Photos/IMG_0001.jpeg", "Photos/IMG_0002.jpeg",
              "Photos/IMG_0003.jpeg"],
    refused: [] });
});

async function show() {
  render(<JobHome job={JOB} onOpenSection={() => {}} onEditSections={() => {}} />);
  await screen.findByRole("heading", { name: JOB });
  await userEvent.click(await screen.findByText("Subject Information"));
}

describe("when the app cannot do what a label asks", () => {
  // Spenser marked a signed engagement letter a subject photograph. The app
  // wrote it down, said "confirmed by you", and did nothing at all with it.
  // It now refuses and says which wall it hit.
  const REFUSAL = "That is a PDF. Only photographs go on the photo pages.";

  it("says why, on the row he clicked", async () => {
    api.setClassification.mockRejectedValue(new Error(REFUSAL));
    await show();
    await userEvent.click(await screen.findByRole("button", { name: "Classify" }));
    await userEvent.click(await screen.findByRole("button", { name: "Subject photograph" }));
    expect(await screen.findByText(REFUSAL)).toBeInTheDocument();
  });

  it("leaves the rest of the screen alone", async () => {
    api.setClassification.mockRejectedValue(new Error(REFUSAL));
    await show();
    await userEvent.click(await screen.findByRole("button", { name: "Classify" }));
    await userEvent.click(await screen.findByRole("button", { name: "Subject photograph" }));
    await screen.findByText(REFUSAL);
    // The whole job used to be replaced by one sentence, which is the right
    // answer when the server has gone and the wrong one for a single refusal.
    expect(screen.getByRole("heading", { name: JOB })).toBeInTheDocument();
    expect(screen.getByText("Signed Engagement Letter.pdf")).toBeInTheDocument();
  });

  it("clears the refusal when he opens the list again", async () => {
    api.setClassification.mockRejectedValue(new Error(REFUSAL));
    await show();
    await userEvent.click(await screen.findByRole("button", { name: "Classify" }));
    await userEvent.click(await screen.findByRole("button", { name: "Subject photograph" }));
    await screen.findByText(REFUSAL);
    await userEvent.click(screen.getByRole("button", { name: "Classify" }));
    await waitFor(() => expect(screen.queryByText(REFUSAL)).not.toBeInTheDocument());
  });

  it("says nothing when the label is one it can act on", async () => {
    await show();
    await userEvent.click(await screen.findByRole("button", { name: "Classify" }));
    await userEvent.click(await screen.findByRole("button", { name: "Engagement letter" }));
    await waitFor(() =>
      expect(api.setClassification).toHaveBeenCalledWith(
        JOB, LETTER.rel, "Engagement letter"));
    expect(screen.queryByText(/Only photographs/)).not.toBeInTheDocument();
  });
});


describe("classifying many files at once", () => {
  // Mason City keeps 57 photographs in one folder. One at a time that is 114
  // clicks. Nothing appears on a row until he asks for it, so the ninety per
  // cent of the time he is not doing this the screen is unchanged.
  const SUBJECT = "Subject photograph";
  const PDF_REASON = "That is a PDF. Only photographs go on the photo pages.";

  beforeEach(() => { api.jobFolders.mockResolvedValue(photosFolder()); });

  it("offers nothing until the folder is open", async () => {
    render(<JobHome job={JOB} onOpenSection={() => {}} onEditSections={() => {}} />);
    await screen.findByRole("heading", { name: JOB });
    expect(screen.queryByRole("button", { name: "Bulk classify" })).not.toBeInTheDocument();
  });

  it("shows no tick boxes until he asks for them", async () => {
    await openPhotos();
    expect(await screen.findByRole("button", { name: "Bulk classify" })).toBeInTheDocument();
    expect(screen.queryAllByRole("checkbox")).toHaveLength(0);
  });

  it("gives every file a tick box when he asks", async () => {
    await openPhotos();
    await userEvent.click(await screen.findByRole("button", { name: "Bulk classify" }));
    expect(screen.getAllByRole("checkbox")).toHaveLength(4);
  });

  it("says how many are ticked", async () => {
    await openPhotos();
    await userEvent.click(await screen.findByRole("button", { name: "Bulk classify" }));
    await userEvent.click(screen.getAllByRole("checkbox")[0]);
    expect(await screen.findByText("1 selected")).toBeInTheDocument();
    await userEvent.click(screen.getAllByRole("checkbox")[1]);
    expect(await screen.findByText("2 selected")).toBeInTheDocument();
  });

  it("ticks the whole folder in one click", async () => {
    await openPhotos();
    await userEvent.click(await screen.findByRole("button", { name: "Bulk classify" }));
    await userEvent.click(screen.getByRole("button", { name: "Select all 4" }));
    expect(await screen.findByText("4 selected")).toBeInTheDocument();
  });

  it("sends every ticked file with the one label", async () => {
    await openPhotos();
    await userEvent.click(await screen.findByRole("button", { name: "Bulk classify" }));
    await userEvent.click(screen.getAllByRole("checkbox")[0]);
    await userEvent.click(screen.getAllByRole("checkbox")[1]);
    await userEvent.click(screen.getByRole("button", { name: "Classify these" }));
    await userEvent.click(await screen.findByRole("button", { name: SUBJECT }));
    await waitFor(() => expect(api.setClassifications).toHaveBeenCalledWith(
      JOB, ["Photos/IMG_0001.jpeg", "Photos/IMG_0002.jpeg"], SUBJECT));
  });

  it("keeps the refused ones ticked, with the reason, and clears the rest", async () => {
    api.setClassifications.mockResolvedValue({
      applied: ["Photos/IMG_0001.jpeg"],
      refused: [{ file: "Photos/Scan.pdf", reason: PDF_REASON }] });
    await openPhotos();
    await userEvent.click(await screen.findByRole("button", { name: "Bulk classify" }));
    await userEvent.click(screen.getByRole("button", { name: "Select all 4" }));
    await userEvent.click(screen.getByRole("button", { name: "Classify these" }));
    await userEvent.click(await screen.findByRole("button", { name: SUBJECT }));
    // Only the one that could not take the label is still waiting, so his next
    // click can give it the label it actually deserves.
    expect(await screen.findByText("1 selected")).toBeInTheDocument();
    expect(screen.getByText(PDF_REASON)).toBeInTheDocument();
  });

  it("clears everything on cancel", async () => {
    await openPhotos();
    await userEvent.click(await screen.findByRole("button", { name: "Bulk classify" }));
    await userEvent.click(screen.getByRole("button", { name: "Select all 4" }));
    await userEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(screen.queryAllByRole("checkbox")).toHaveLength(0);
    expect(await screen.findByRole("button", { name: "Bulk classify" })).toBeInTheDocument();
  });

  it("forgets the ticks when the folder is closed", async () => {
    await openPhotos();
    await userEvent.click(await screen.findByRole("button", { name: "Bulk classify" }));
    await userEvent.click(screen.getByRole("button", { name: "Select all 4" }));
    await userEvent.click(screen.getByText("Photos"));      // close it
    await userEvent.click(await screen.findByText("Photos"));  // open it again
    expect(screen.queryAllByRole("checkbox")).toHaveLength(0);
    expect(screen.queryByText("4 selected")).not.toBeInTheDocument();
  });

  it("brings the section count back up to date", async () => {
    // Classifying photographs in changes what the section on the right holds.
    // Refreshing only the left band left the count beside Subject Photographs
    // stale until he reloaded the page.
    api.jobDetail.mockResolvedValue({
      name: JOB, photo_count: 12, context: "", engagement: "", sections: [] });
    await openPhotos();
    await userEvent.click(await screen.findByRole("button", { name: "Bulk classify" }));
    await userEvent.click(screen.getByRole("button", { name: "Select all 4" }));
    await userEvent.click(screen.getByRole("button", { name: "Classify these" }));
    await userEvent.click(await screen.findByRole("button", { name: SUBJECT }));
    await waitFor(() => expect(api.jobDetail).toHaveBeenCalledTimes(2));
  });

  it("leaves the single file path alone", async () => {
    await openPhotos();
    expect(await screen.findAllByRole("button", { name: "Classify" })).toHaveLength(4);
  });
});

test("both sections open, and each one says which it is", async () => {
  // The row used to be a single hardcoded string. It is a list now, and a
  // test that never clicked it let a renamed prop through unnoticed.
  const opened = [];
  render(<JobHome job={JOB} onOpenSection={(k) => opened.push(k)} onEditSections={() => {}} />);
  await screen.findByRole("heading", { name: JOB });
  await userEvent.click(await screen.findByRole("button", { name: /Subject Photographs/ }));
  await userEvent.click(await screen.findByRole("button", { name: /Description of Improvements/ }));
  expect(opened).toEqual(["photos", "improvements"]);
});

test("Description of Improvements is no longer listed as unavailable", async () => {
  render(<JobHome job={JOB} onOpenSection={() => {}} onEditSections={() => {}} />);
  await screen.findByRole("button", { name: /Description of Improvements/ });
  expect(screen.queryByText(/Not available in this pilot/)).toBeNull();
});
