import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";

import ChooseFolder from "./ChooseFolder.jsx";
import * as api from "../api.js";

// One place a folder listing is made, so a test says only what is different
// about the folder it cares about.
function listing(over = {}) {
  return {
    path: "/Users/mark/RRF Jobs", label: "RRF Jobs", parent: "/Users/mark",
    breadcrumbs: [{ label: "/", path: "/" }, { label: "RRF Jobs", path: "/Users/mark/RRF Jobs" }],
    folders: [], readable: true, is_drive_list: false, loose_files: 0,
    message: "", job_count: 0, is_root: false, is_home: false, is_job: false,
    ...over,
  };
}

const JOB_ROWS = [
  { name: "ANYTOWN_100 Example Avenue - 2026", path: "/j/1", is_job: true },
  { name: "ANYTOWN_200 Example Avenue - 2026", path: "/j/2", is_job: true },
];

beforeEach(() => {
  vi.spyOn(api, "browseFolders");
  vi.spyOn(api, "saveWorkspace").mockResolvedValue({ valid: true });
});

async function show(over) {
  api.browseFolders.mockResolvedValue(listing(over));
  render(<ChooseFolder first onSaved={() => {}} />);
  await screen.findByRole("button", { name: /use (this|as new)/i });
}

describe("a folder holding jobs", () => {
  it("says how many it found and offers to use it", async () => {
    await show({ folders: JOB_ROWS, job_count: 2 });
    expect(screen.getByText("2 jobs found")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Use this folder" })).toBeEnabled();
  });

  it("saves that exact folder when pressed", async () => {
    await show({ folders: JOB_ROWS, job_count: 2 });
    await userEvent.click(screen.getByRole("button", { name: "Use this folder" }));
    expect(api.saveWorkspace).toHaveBeenCalledWith("/Users/mark/RRF Jobs", false);
  });

  it("marks which rows are jobs, by name, for a screen reader", async () => {
    await show({
      folders: [...JOB_ROWS, { name: "Old paperwork", path: "/j/3", is_job: false }],
      job_count: 2,
    });
    expect(screen.getByRole("button", { name: "Open job folder ANYTOWN_100 Example Avenue - 2026" }))
      .toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Open folder Old paperwork" })).toBeInTheDocument();
  });
});

describe("a folder holding no jobs", () => {
  it("cannot be used, and says what to do instead", async () => {
    await show({ folders: [{ name: "Downloads", path: "/d", is_job: false }] });
    expect(screen.getByText("No jobs found here")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Use this folder" })).toBeDisabled();
    expect(screen.getByText(/Open one of the folders below/)).toBeInTheDocument();
  });

  it("saves nothing when the disabled button is clicked", async () => {
    await show({ folders: [{ name: "Downloads", path: "/d", is_job: false }] });
    await userEvent.click(screen.getByRole("button", { name: "Use this folder" }));
    expect(api.saveWorkspace).not.toHaveBeenCalled();
  });
});

describe("an empty folder", () => {
  it("offers a different button, in its own words", async () => {
    await show({ folders: [] });
    expect(screen.getByRole("button", { name: "Use as new jobs folder" })).toBeEnabled();
    expect(screen.queryByRole("button", { name: "Use this folder" })).toBeNull();
  });

  it("tells the server the choice was deliberate", async () => {
    await show({ folders: [] });
    await userEvent.click(screen.getByRole("button", { name: "Use as new jobs folder" }));
    expect(api.saveWorkspace).toHaveBeenCalledWith("/Users/mark/RRF Jobs", true);
  });
});

describe("the three that are never the jobs folder", () => {
  it("refuses the top of the disk", async () => {
    await show({ is_root: true, folders: [{ name: "Users", path: "/Users", is_job: false }] });
    expect(screen.getByRole("button", { name: "Use this folder" })).toBeDisabled();
    expect(screen.getByText(/top of the disk/)).toBeInTheDocument();
  });

  it("refuses the home folder", async () => {
    await show({ is_home: true, folders: [{ name: "Desktop", path: "/d", is_job: false }] });
    expect(screen.getByRole("button", { name: "Use this folder" })).toBeDisabled();
    expect(screen.getByText(/your home folder/)).toBeInTheDocument();
  });

  it("refuses a single job folder, and does not offer the empty-folder way in", async () => {
    await show({ is_job: true, folders: [] });
    expect(screen.queryByRole("button", { name: "Use as new jobs folder" })).toBeNull();
    expect(screen.getByRole("button", { name: "Use this folder" })).toBeDisabled();
    expect(screen.getByText(/looks like one job/)).toBeInTheDocument();
  });
});

describe("when the server refuses", () => {
  it("shows the server's own sentence and saves nothing", async () => {
    api.saveWorkspace.mockRejectedValue(new Error("No jobs were found in here."));
    await show({ folders: [] });
    await userEvent.click(screen.getByRole("button", { name: "Use as new jobs folder" }));
    await waitFor(() =>
      expect(screen.getByText("No jobs were found in here.")).toBeInTheDocument());
  });
});
