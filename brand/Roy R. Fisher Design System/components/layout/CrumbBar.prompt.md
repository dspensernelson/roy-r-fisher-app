Charcoal breadcrumb bar — one per screen, directly under the Masthead.

```jsx
<CrumbBar trail={[{ label: "Jobs", onClick: goJobs }, { label: "MASON CITY_4151 4th St SW" }]}
  right={<button className="rrf-crumb" onClick={openSettings}>Settings</button>} />
```

The current crumb has no `onClick`. In this app the screen's actions live in `ScreenHead` rather than here, so the bar stays purely positional.
