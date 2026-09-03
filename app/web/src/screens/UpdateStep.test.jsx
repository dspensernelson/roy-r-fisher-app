import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";

import UpdateStep, { megabytes } from "./UpdateStep.jsx";
import * as api from "../api.js";

const SIZE = 55939858;   // the real v0.5.3 package, 53 MB

function open(over = {}) {
  return render(<UpdateStep version="0.5.3" available="0.5.4" size={SIZE}
                            onClose={() => {}} {...over} />);
}

function progress(over = {}) {
  return { running: true, stage: "Downloading", done: 0, total: SIZE,
           error: "", version: "0.5.4", cancelling: false, ...over };
}

beforeEach(() => { vi.restoreAllMocks(); });

describe("what he is told before he agrees", () => {
  it("names the version and what the download costs", () => {
    open();
    expect(screen.getByText(/Update to version 0\.5\.4\?/)).toBeInTheDocument();
    expect(screen.getByText(/about 53 MB/)).toBeInTheDocument();
    expect(screen.getByText(/You are on version 0\.5\.3/)).toBeInTheDocument();
  });

  it("says his work is not inside the app", () => {
    open();
    expect(screen.getByText(/not kept inside the app and are not touched/))
      .toBeInTheDocument();
  });

  it("says what the checksum does and does not prove", () => {
    // The same honesty the manifest check is already held to. Without code
    // signing this catches a damaged download, not somebody who can rewrite
    // the file and the checksum together.
    open();
    expect(screen.getByText(/does not prove who made/)).toBeInTheDocument();
    expect(screen.getByText(/damaged or incomplete download/)).toBeInTheDocument();
    // Plain words. "Checksum" is a term he would not recognise, and
    // HOW-WE-WORK calls that a defect in the writing.
    expect(screen.queryByText(/checksum/i)).toBeNull();
  });

  it("says nothing changes if it goes wrong", () => {
    open();
    expect(screen.getByText(/the version you have now is not touched/i))
      .toBeInTheDocument();
  });

  it("does not start anything until he clicks", () => {
    const start = vi.spyOn(api, "startUpdate");
    open();
    expect(start).not.toHaveBeenCalled();
  });

  it("Not now closes the step and starts nothing", async () => {
    const start = vi.spyOn(api, "startUpdate");
    const closed = vi.fn();
    open({ onClose: closed });
    await userEvent.click(screen.getByRole("button", { name: "Not now" }));
    expect(closed).toHaveBeenCalled();
    expect(start).not.toHaveBeenCalled();
  });
});

describe("while it runs", () => {
  it("shows megabytes of the total rather than a bar that says nothing", async () => {
    vi.spyOn(api, "startUpdate").mockResolvedValue({});
    vi.spyOn(api, "updateProgress").mockResolvedValue(
      progress({ done: 12 * 1024 * 1024 }));
    open();
    await userEvent.click(screen.getByRole("button", { name: "Update now" }));
    await waitFor(() =>
      expect(screen.getByText("Downloading 12 MB of 53 MB")).toBeInTheDocument());
  });

  it("names each stage in words", async () => {
    vi.spyOn(api, "startUpdate").mockResolvedValue({});
    vi.spyOn(api, "updateProgress").mockResolvedValue(
      progress({ stage: "Checking the download" }));
    open();
    await userEvent.click(screen.getByRole("button", { name: "Update now" }));
    await waitFor(() =>
      expect(screen.getByText("Checking the download")).toBeInTheDocument());
  });

  it("offers a Cancel while it is downloading", async () => {
    vi.spyOn(api, "startUpdate").mockResolvedValue({});
    vi.spyOn(api, "updateProgress").mockResolvedValue(progress());
    const cancel = vi.spyOn(api, "cancelUpdate").mockResolvedValue({});
    open();
    await userEvent.click(screen.getByRole("button", { name: "Update now" }));
    await waitFor(() => screen.getByRole("button", { name: "Cancel" }));
    await userEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(cancel).toHaveBeenCalled();
  });

  it("does not offer a Cancel once it has moved past the download", async () => {
    vi.spyOn(api, "startUpdate").mockResolvedValue({});
    vi.spyOn(api, "updateProgress").mockResolvedValue(
      progress({ stage: "Installing" }));
    open();
    await userEvent.click(screen.getByRole("button", { name: "Update now" }));
    await waitFor(() => screen.getByText("Installing"));
    expect(screen.queryByRole("button", { name: "Cancel" })).toBeNull();
  });
});

describe("how it ends", () => {
  it("says the app is closing and names the Desktop icon", async () => {
    vi.spyOn(api, "startUpdate").mockResolvedValue({});
    vi.spyOn(api, "updateProgress").mockResolvedValue(
      progress({ running: false, stage: "Closing" }));
    open();
    await userEvent.click(screen.getByRole("button", { name: "Update now" }));
    await waitFor(() => expect(screen.getByText("Installing the new version.")).toBeInTheDocument());
    // It says the app closed itself on purpose, rather than leaving a person
    // to guess why the screen stopped answering.
    expect(screen.getByText(/The app has closed itself/)).toBeInTheDocument();
    // And that this tab is finished with, which is the thing that was missing:
    // it used to sit for ever over a job list that still looked usable.
    expect(screen.getByText(/You can close this tab/)).toBeInTheDocument();
    expect(screen.getByText(/Roy R\. Fisher icon on your Desktop/))
      .toBeInTheDocument();
  });

  it("shows a failure as one sentence he can read", async () => {
    vi.spyOn(api, "startUpdate").mockResolvedValue({});
    vi.spyOn(api, "updateProgress").mockResolvedValue(progress({
      running: false, stage: "",
      error: "The update did not arrive intact and was not installed." }));
    open();
    await userEvent.click(screen.getByRole("button", { name: "Update now" }));
    await waitFor(() => expect(
      screen.getByText(/did not arrive intact/)).toBeInTheDocument());
    expect(screen.getByRole("button", { name: "Close" })).toBeInTheDocument();
  });

  it("shows a refusal to start as one sentence", async () => {
    vi.spyOn(api, "startUpdate").mockRejectedValue(
      new Error("An update is already running."));
    open();
    await userEvent.click(screen.getByRole("button", { name: "Update now" }));
    await waitFor(() => expect(
      screen.getByText("An update is already running.")).toBeInTheDocument());
  });

  it("treats the app going quiet as the ending it asked for", async () => {
    // The successful ending is the app closing itself, so the last poll before
    // it goes will not answer. That is not an error to put on his screen.
    vi.spyOn(api, "startUpdate").mockResolvedValue({});
    vi.spyOn(api, "updateProgress")
      .mockResolvedValueOnce(progress({ running: false, stage: "Closing" }))
      .mockRejectedValue(new Error("Failed to fetch"));
    open();
    await userEvent.click(screen.getByRole("button", { name: "Update now" }));
    await waitFor(() => screen.getByText("Installing the new version."));
    expect(screen.queryByText(/Failed to fetch/)).toBeNull();
  });
});

describe("megabytes", () => {
  it("reads the real package as 53 MB", () => {
    expect(megabytes(SIZE)).toBe("53 MB");
  });

  it("says nothing rather than nonsense when there is no size", () => {
    expect(megabytes(0)).toBe("");
    expect(megabytes(undefined)).toBe("");
    expect(megabytes(-1)).toBe("");
  });
});
