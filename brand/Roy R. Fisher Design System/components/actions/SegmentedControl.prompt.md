Two-way switch shown inside a step, not parked in settings.

```jsx
<SegmentedControl value={style} onChange={setStyle}
  options={[{ key: "view", label: "View", flag: "suggested" }, { key: "facing", label: "Facing" }]} />
```

Full width of the column it controls. Two options is the norm; three is the maximum.

`flag` renders above the control as a ruled caption over the option it names, so the recommendation reads as a note on the box rather than part of the label. The control reserves 20px of headroom for it automatically — leave room above.
