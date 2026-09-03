import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import Settings from "./Settings.jsx";
import * as api from "../api.js";

const WORKSPACE = { path: "C:\\Jobs", folder_count: 4, source: "saved" };

beforeEach(() => {
  vi.spyOn(api, "getSettings").mockResolvedValue({ key_set: true, ends_with: "ab12" });
});

describe("Check now", () => {
  it("tells the rest of the app to look again", async () => {
    // Found 2026-09-03 on Spenser's virtual machine. Check now said "Version
    // 0.6.4 is available. Use the Update available button at the top of the
    // screen" and there was no such button, because the masthead asks the
    // server about updates once at load and nothing told it to ask again.
    vi.spyOn(api, "checkForUpdate").mockResolvedValue({ available: "0.6.4" });
    const onUpdateChecked = vi.fn().mockResolvedValue(undefined);

    render(<Settings workspace={WORKSPACE} version="0.6.3"
                     onChangeFolder={() => {}} onWorkspaceChanged={() => {}}
                     onUpdateChecked={onUpdateChecked} />);
    await userEvent.click(await screen.findByRole("button", { name: "Check now" }));

    expect(await screen.findByText(/Version 0.6.4 is available/)).toBeInTheDocument();
    expect(onUpdateChecked).toHaveBeenCalled();
  });

  it("still works when nothing is listening", async () => {
    vi.spyOn(api, "checkForUpdate").mockResolvedValue({ available: "" });
    render(<Settings workspace={WORKSPACE} version="0.6.4"
                     onChangeFolder={() => {}} onWorkspaceChanged={() => {}} />);
    await userEvent.click(await screen.findByRole("button", { name: "Check now" }));
    expect(await screen.findByText("You are on the newest version.")).toBeInTheDocument();
  });
});
