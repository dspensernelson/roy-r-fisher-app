/**
 * One rule for a money figure on the photographs screen. Spenser, 2026-09-18:
 * from $10 up it is whole dollars, rounded UP, never down, so a shown price is
 * never lower than the arithmetic behind it. Under $10 each place keeps the
 * shape it had: pennies as cents where the screen already said cents, and
 * dollars and cents everywhere else.
 */
import { describe, it, expect } from "vitest";
import { showMoney } from "./money.js";

describe("under $10, as it was", () => {
  it("says pennies as cents where asked", () => {
    expect(showMoney(0.06, { cents: true })).toBe("6¢");
    expect(showMoney(0.4, { cents: true })).toBe("40¢");
  });

  it("says dollars and cents otherwise", () => {
    expect(showMoney(0.15)).toBe("$0.15");
    expect(showMoney(3.05)).toBe("$3.05");
    expect(showMoney(3.05, { cents: true })).toBe("$3.05");
    expect(showMoney(9.99)).toBe("$9.99");
  });
});

describe("from $10 up, whole dollars, rounded up", () => {
  it("rounds up, never down", () => {
    expect(showMoney(12.34)).toBe("$13");
    expect(showMoney(10.01)).toBe("$11");
    expect(showMoney(99.5, { cents: true })).toBe("$100");
  });

  it("leaves a whole dollar alone", () => {
    expect(showMoney(10)).toBe("$10");
    expect(showMoney(12.0)).toBe("$12");
  });

  it("is not pushed up a dollar by a float that is a hair over", () => {
    // 0.1 + 0.2 style noise: 12.000000000001 is twelve dollars.
    expect(showMoney(12 + 1e-12)).toBe("$12");
  });
});

describe("nothing to show", () => {
  it("gives null for no figure", () => {
    expect(showMoney(null)).toBeNull();
    expect(showMoney(undefined)).toBeNull();
  });
});
