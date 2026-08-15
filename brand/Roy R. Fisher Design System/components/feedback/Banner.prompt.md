Inline result and caution messages. Never a floating toast — the message stays on the screen it belongs to.

```jsx
<Banner tone="done">Done. <strong>Photo Pages.docx</strong> was created in this job's Photos folder. Nothing was overwritten.</Banner>
<Banner tone="warn">We have only one finished report of this kind on file, so this list is a starting point.</Banner>
```

Errors name the fix ("Close this tab and start the app again"), never a code. The glyph is chosen by tone — pass `sprite` when the page is not at the design system root.
