/**
 * How a money figure is shown on the photographs screen. The one place.
 *
 * From $10 up it is whole dollars, rounded UP and never down. Spenser,
 * 2026-09-18. A shown price is never lower than the arithmetic behind it,
 * which is the rule every figure in this app already keeps, and whole dollars
 * are what let the widget's bar hold a three-digit count and the money on one
 * line.
 *
 * Under $10 each place keeps the shape it had: `cents` for the places that
 * already said pennies as cents (the bar and the refresh on a photograph),
 * dollars and cents for the rest (the Generate captions window).
 */
export function showMoney(n, { cents = false } = {}) {
  if (n === null || n === undefined || Number.isNaN(n)) return null;
  const inCents = Math.round(n * 100);
  // Up, never down, even by a fraction of a cent: $12.004 is $13. Only float
  // noise is forgiven, so 12.000000000001 is twelve dollars, not thirteen.
  if (inCents >= 1000) return `$${Math.ceil(n - 1e-9)}`;
  if (cents && inCents < 100) return `${inCents}¢`;
  return `$${(inCents / 100).toFixed(2)}`;
}
