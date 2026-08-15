Every screen's outer frame — masthead, crumb bar, 1200px content frame.

```jsx
<AppShell trail={[{ label: "Jobs" }]}><ScreenHead title="Jobs" /></AppShell>
```

The 1200px width is deliberate (the job screen compares two columns of wrapping text); do not narrow it to 960.
