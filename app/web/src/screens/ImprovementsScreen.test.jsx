import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { test, expect, vi, beforeEach } from "vitest";

import ImprovementsScreen from "./ImprovementsScreen.jsx";
import * as api from "../api.js";

vi.mock("../api.js");

const JOB = "BURLINGTON_425 Valley St, (Blaul Lofts)";

const SOURCES = {
  ai_available: true, ready: true,
  cards: [{ rel: "Subject Information/PRC_425 Valley St.pdf", name: "PRC_425 Valley St.pdf" }],
  transcripts: [{ rel: "Transcripts/TRANSCRIPT Improvements.docx", name: "TRANSCRIPT Improvements.docx" }],
};

const FOUND = {
  parts: ["Common Areas"],
  refused: 1,
  found: [
    { block: "BUILDING EXTERIOR", part: "", field: "Foundation",
      value: "Brick and concrete.", source: "card", quote: "Brick or Stone" },
    { block: "BUILDING EXTERIOR", part: "", field: "Foundation",
      value: "Brick and concrete.", source: "transcript", quote: "rock and rubble" },
    { block: "BUILDING EXTERIOR", part: "", field: "Roof",
      value: "Rubber membrane on wood.", source: "card", quote: "Rubber Membrane/Wood" },
    { block: "GENERAL", part: "", field: "Building area",
      value: "70,607 sq.ft.", source: "card", quote: "GBA 70607" },
  ],
};

beforeEach(() => {
  vi.resetAllMocks();
  api.improvementSources.mockResolvedValue(SOURCES);
  api.improvementState.mockResolvedValue({ blocks: [], read: false });
  api.saveImprovements.mockResolvedValue({ saved: true });
  api.readImprovements.mockImplementation((job, body) =>
    Promise.resolve(body.confirmed
      ? { ...FOUND, card: "PRC_425 Valley St.pdf", transcript: "TRANSCRIPT Improvements.docx" }
      : { confirm: true, card: "PRC_425 Valley St.pdf",
          transcript: "TRANSCRIPT Improvements.docx", characters: 27128 }));
  api.writeParagraph.mockResolvedValue({ text: "The building is a brick warehouse." });
});

async function readThem() {
  render(<ImprovementsScreen job={JOB} onBack={() => {}} />);
  await userEvent.click(await screen.findByRole("button", { name: "Read them" }));
  await userEvent.click(await screen.findByRole("button", { name: "Send them" }));
}

test("nothing is read until he presses the button", async () => {
  render(<ImprovementsScreen job={JOB} onBack={() => {}} />);
  await screen.findByText("Ready to make");
  expect(api.readImprovements).not.toHaveBeenCalled();
});

test("it says what it will send before it sends it", async () => {
  render(<ImprovementsScreen job={JOB} onBack={() => {}} />);
  await userEvent.click(await screen.findByRole("button", { name: "Read them" }));
  expect(await screen.findByText(/27,128 characters/)).toBeTruthy();
  // Asked, not sent. The second call is the one that spends.
  expect(api.readImprovements).toHaveBeenCalledWith(JOB,
    expect.objectContaining({ confirmed: false }));
});

test("he can back out of sending", async () => {
  render(<ImprovementsScreen job={JOB} onBack={() => {}} />);
  await userEvent.click(await screen.findByRole("button", { name: "Read them" }));
  await userEvent.click(screen.getByRole("button", { name: "Not yet" }));
  expect(await screen.findByRole("button", { name: "Read them" })).toBeTruthy();
});

test("a job with no key is told plainly, and cannot spend", async () => {
  api.improvementSources.mockResolvedValue({ ...SOURCES, ai_available: false });
  render(<ImprovementsScreen job={JOB} onBack={() => {}} />);
  expect(await screen.findByText(/needs a key on this computer/)).toBeTruthy();
  expect(screen.queryByRole("button", { name: "Read them" })).toBeNull();
});

test("both documents agreeing is one row with two ticks", async () => {
  await readThem();
  const rows = await screen.findAllByText("Foundation");
  expect(rows).toHaveLength(1);
  // Roof has a PRC tick too, so the transcript tick is the telling one: only
  // Foundation is supported by both documents.
  expect(await screen.findAllByTitle("show the words from the PRC")).toHaveLength(3);
  expect(await screen.findAllByTitle("show the words from the transcript")).toHaveLength(1);
});

test("the words behind a tick appear only when he asks", async () => {
  await readThem();
  const quoted = () => Array.from(document.querySelectorAll(".q"))
                            .map((el) => el.textContent);
  expect(quoted()).toEqual([]);
  // The tick on Foundation's own row, not whichever tick happens to be first.
  const row = (await screen.findByText("Foundation")).closest(".f");
  await userEvent.click(row.querySelector('[title="show the words from the PRC"]'));
  expect(quoted().join(" ")).toContain("Brick or Stone");
});

test("what the documents do not say is counted, not shown as a value", async () => {
  await readThem();
  expect(await screen.findByText(/1 value was left out/)).toBeTruthy();
});

test("the Word file waits until both paragraphs are approved", async () => {
  await readThem();
  const make = await screen.findByRole("button", { name: "Make the Word file" });
  expect(make.disabled).toBe(true);
  expect(await screen.findByText(/waits on GENERAL and CONCLUSION/)).toBeTruthy();
});

test("writing a paragraph sends only the ticked facts and the notes", async () => {
  await readThem();
  await userEvent.click((await screen.findAllByRole("button", { name: "Write this paragraph" }))[0]);
  expect(api.writeParagraph).toHaveBeenCalledWith(JOB, expect.objectContaining({
    block: "GENERAL", facts: ["70,607 sq.ft."], notes: "" }));
});

test("a written paragraph is not approved until he says so", async () => {
  await readThem();
  await userEvent.click((await screen.findAllByRole("button", { name: "Write this paragraph" }))[0]);
  expect(await screen.findByText("Not approved yet")).toBeTruthy();
  await userEvent.click(await screen.findByRole("button", { name: "Approve this paragraph" }));
  expect(await screen.findByText(/Approved/)).toBeTruthy();
});

test("coming back to a job he has read shows his own work, and spends nothing", async () => {
  api.improvementState.mockResolvedValue({
    read: true,
    blocks: [{ name: "GENERAL", part: "", on: true, notes: "", draft: "Mine.",
               approved: true, fields: [] },
             { name: "CONCLUSION", part: "", on: true, notes: "", draft: "Also mine.",
               approved: true, fields: [] }],
  });
  render(<ImprovementsScreen job={JOB} onBack={() => {}} />);
  // Once in the box he can edit, once on the page that prints.
  expect(await screen.findByDisplayValue("Mine.")).toBeTruthy();
  const printed = await screen.findByText("Mine.", { selector: ".paper p" });
  expect(printed).toBeTruthy();
  expect(api.readImprovements).not.toHaveBeenCalled();
  const make = await screen.findByRole("button", { name: "Make the Word file" });
  expect(make.disabled).toBe(false);
});
