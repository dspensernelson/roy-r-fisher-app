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

function folders(over = {}) {
  return {
    typical: [{ folder: "Subject Information", count: 1, unreadable: false,
                truncated: false, kind: "folder", files: [LETTER] }],
    other: [], root_files: [], missing_classifications: [], ...over,
  };
}

beforeEach(() => {
  vi.spyOn(api, "jobDetail").mockResolvedValue({
    name: JOB, photo_count: 12, context: "", engagement: "", sections: [] });
  vi.spyOn(api, "jobFolders").mockResolvedValue(folders());
  vi.spyOn(api, "classificationLabels").mockResolvedValue({
    labels: ["Engagement letter", "Subject photograph"] });
  vi.spyOn(api, "setClassification").mockResolvedValue({ ok: true });
  vi.spyOn(api, "clearClassification").mockResolvedValue({ ok: true });
});

async function show() {
  render(<JobHome job={JOB} onOpenPhotos={() => {}} onEditSections={() => {}} />);
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
