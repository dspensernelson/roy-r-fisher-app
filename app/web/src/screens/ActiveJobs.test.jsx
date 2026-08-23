import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";

import ActiveJobs from "./ActiveJobs.jsx";
import * as api from "../api.js";

const FOLDERS = ["ANYTOWN_100 Example Avenue - 2026", "ANYTOWN_200 Example Avenue - 2026"];

beforeEach(() => {
  vi.spyOn(api, "getWorkspaceFolders").mockResolvedValue({
    parent: "/Users/mark/RRF Jobs", folders: FOLDERS, active: [], missing: [],
  });
  vi.spyOn(api, "putWorkspaceFolders").mockResolvedValue({ active: [] });
});

async function show() {
  render(<ActiveJobs first onDone={() => {}} />);
  await screen.findByRole("button", { name: /Use these active jobs/ });
}

it("starts with nothing chosen and will not carry on", async () => {
  await show();
  expect(screen.getByText("0 of 2 active")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /Use these active jobs/ })).toBeDisabled();
  expect(screen.getByText(/Pick at least one job/)).toBeInTheDocument();
});

it("saves nothing if the disabled button is pressed", async () => {
  await show();
  await userEvent.click(screen.getByRole("button", { name: /Use these active jobs/ }));
  expect(api.putWorkspaceFolders).not.toHaveBeenCalled();
});

it("comes alive as soon as one job is picked", async () => {
  await show();
  await userEvent.click(screen.getByRole("button", { name: FOLDERS[0] }));
  expect(screen.getByText("1 of 2 active")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /Use these active jobs/ })).toBeEnabled();
  expect(screen.queryByText(/Pick at least one job/)).toBeNull();
});

it("saves exactly the jobs that were ticked", async () => {
  await show();
  await userEvent.click(screen.getByRole("button", { name: FOLDERS[1] }));
  await userEvent.click(screen.getByRole("button", { name: /Use these active jobs/ }));
  expect(api.putWorkspaceFolders).toHaveBeenCalledWith([FOLDERS[1]]);
});

it("select all takes every job, clear all puts it back to none", async () => {
  await show();
  await userEvent.click(screen.getByRole("button", { name: /Select all 2 jobs/ }));
  expect(screen.getByText("2 of 2 active")).toBeInTheDocument();
  await userEvent.click(screen.getByRole("button", { name: "Clear all" }));
  expect(screen.getByText("0 of 2 active")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /Use these active jobs/ })).toBeDisabled();
});

it("searching narrows the list without changing what is ticked", async () => {
  await show();
  await userEvent.click(screen.getByRole("button", { name: FOLDERS[0] }));
  await userEvent.type(screen.getByPlaceholderText("Find a job by name"), "200");
  expect(screen.queryByRole("button", { name: FOLDERS[0] })).toBeNull();
  expect(screen.getByRole("button", { name: FOLDERS[1] })).toBeInTheDocument();
  expect(screen.getByText(/1 of 2 active/)).toBeInTheDocument();
});
