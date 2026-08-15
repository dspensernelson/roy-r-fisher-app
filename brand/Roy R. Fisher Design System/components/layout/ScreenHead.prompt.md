The title row at the top of every screen, with the screen's actions on the same line.

```jsx
<ScreenHead title="Photos" sub="14 photos, about 5 pages. Drag a photo to reorder it."
  actions={<><Button>Build photo pages</Button><LinkButton>Add photos</LinkButton></>}
  below={busy ? <Working label={busy} /> : null} />
```

No hero areas above it. Progress goes in `below`, never in place of the actions.
