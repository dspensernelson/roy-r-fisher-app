/**
 * Every money figure on the photographs screen, from $10 up, is whole
 * dollars rounded up. Spenser, 2026-09-18. And the Clear captions window no
 * longer says cleared captions cannot be recovered, which stopped being true
 * when Restore cleared captions arrived.
 */
import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, afterEach } from "vitest";

import PhotosScreen from "./PhotosScreen.jsx";
import * as api from "../api.js";

const JOB = "ANYTOWN_100 Example Avenue - 2026";

function photos(n, caption = "") {
  return Array.from({ length: n }, (_, i) => ({
    file: `p${String(i + 1).padStart(3, "0")}.jpg`, caption,
    ...(caption ? { author: "ai" } : {}) }));
}

function setUp({ list, total, one }) {
  vi.spyOn(api, "getManifest").mockResolvedValue({
    job: JOB, context: "", report_year: 2026, caption_style: "view",
    photos: list, photos_per_page: 3 });
  vi.spyOn(api, "jobFacts").mockResolvedValue({
    ready: true, city: "Anytown", address: "100 Example Avenue",
    filename: "Anytown_100 Example Avenue Photos (Complete).docx", missing: [] });
  vi.spyOn(api, "captionEstimate").mockResolvedValue({
    photos_to_send: list.filter((p) => !p.caption).length, tranches: 5, tranche_size: 60,
    needs_confirmation: true, confirm_above: 30,
    estimate: { label: "Estimated maximum cost", total },
    one_photo: { total: one },
    ai_available: true, blocked_because: "",
    samples: { photos: 0, styles: 2, estimate: { total: 0 } } });
  vi.spyOn(api, "captionStyles").mockResolvedValue({ ai_available: true, styles: [] });
  vi.spyOn(api, "captionSamples").mockResolvedValue({ samples: [] });
  vi.spyOn(api, "photoGroups").mockResolvedValue({
    groups: [{ folder: "", count: list.length, sample: list[0].file }],
    chosen: null, chosen_missing: false, needs_choice: false });
  vi.spyOn(api, "readingProgress").mockResolvedValue({ reading: false, done: 0, total: 0 });
  render(<PhotosScreen job={JOB} onBack={() => {}} />);
}

afterEach(() => vi.restoreAllMocks());

describe("from $10 up, whole dollars rounded up, everywhere", () => {
  it("in the bar", async () => {
    setUp({ list: photos(250), total: 12.34, one: 0.05 });
    await waitFor(() => expect(document.querySelector(".money")).toBeTruthy());
    expect(document.querySelector(".money").textContent).toBe("~$13");
  });

  it("in the Generate captions window, the corner and the button", async () => {
    setUp({ list: photos(250), total: 12.34, one: 0.05 });
    await userEvent.click(await screen.findByRole("button", { name: /Generate captions/ }));
    await waitFor(() => expect(document.querySelector(".sheet-cost")).toBeTruthy());
    expect(document.querySelector(".sheet-cost").textContent).toBe("$13 max");
    expect(screen.getByRole("button", { name: "Generate captions ($13)" })).toBeInTheDocument();
  });

  it("on a photograph's refresh", async () => {
    setUp({ list: photos(3, "View"), total: 0.15, one: 10.2 });
    await waitFor(() => expect(document.querySelector(".refresh-dot .price")).toBeTruthy());
    expect(document.querySelector(".refresh-dot .price").textContent).toBe("~$11");
  });

  it("and under $10 nothing changes", async () => {
    setUp({ list: photos(61), total: 3.05, one: 0.05 });
    await waitFor(() => expect(document.querySelector(".money")).toBeTruthy());
    expect(document.querySelector(".money").textContent).toBe("~$3.05");
    expect(document.querySelector(".refresh-dot .price").textContent).toBe("~5¢");
  });
});

describe("the Clear captions window", () => {
  it("no longer says they cannot be recovered, and keeps its other words", async () => {
    setUp({ list: photos(3, "View"), total: 0.15, one: 0.05 });
    await userEvent.click(await screen.findByRole("button", { name: "Clear captions" }));
    const sheet = await screen.findByRole("dialog", { name: "Clear the captions?" });
    expect(sheet.textContent).not.toMatch(/cannot be recovered/);
    expect(sheet.querySelector(".fine").textContent.trim())
      .toBe("The photographs, their order and the caption style are unchanged.");
  });
});
