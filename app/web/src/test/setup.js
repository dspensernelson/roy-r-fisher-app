// Matchers like toBeDisabled and toBeInTheDocument, which say what they mean
// when they fail.
import "@testing-library/jest-dom/vitest";

// Nothing in a UI test may reach the network. Every screen here is handed the
// answers it should get; an unmocked call is a bug in the test and should look
// like one rather than hanging.
beforeEach(() => {
  globalThis.fetch = vi.fn(() =>
    Promise.reject(new Error("a UI test tried to call the network")));
});
